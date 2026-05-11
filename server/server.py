import base64
from datetime import datetime
import json
import os
import socket
from threading import Thread

from dotenv import load_dotenv

from database.crud import get_genres, get_genre, add_genre, delete_genres
from database.crud import get_books, add_book, delete_book, update_book
from database.crud import authenticate_user, register_user
from database.database import SessionLocal, init_db
from database.database import BookTable

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, os.getenv("COVERS_DIR", "content/covers"))
BOOKS_DIR = os.path.join(BASE_DIR, os.getenv("BOOKS_DIR", "content/books"))

# Множество команд, требующих прав администратора.
ADMIN_ONLY_COMMANDS: frozenset[str] = frozenset({
    "add_genre",
    "delete_genres",
    "add_book",
    "delete_book",
    "edit_book",
})


def fetch_file_json(file_path: str) -> str:
    """Формирование JSON для передачи одной полноценной книги"""
    full_path = os.path.join(BOOKS_DIR, file_path)

    if not os.path.exists(full_path):
        return json.dumps({
            "status": "error",
            "message": f"Файл '{file_path}' не найден на сервере"
        }, ensure_ascii=False)

    with open(full_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    return json.dumps({
        "status": "success",
        "action": "download",
        "filename": os.path.basename(file_path),
        "file_data": encoded
    }, ensure_ascii=False)


def fetch_books_json() -> str:
    """Формирование JSON для передачи информации о всех книгах для карточек"""
    try:
        with SessionLocal() as session:
            books = get_books(session)
            result = []
            for b in books:
                try:
                    # Формируем дату безопасно
                    p_date = b.public_date.strftime("%d.%m.%Y") if b.public_date else "Дата неизвестна"

                    result.append({
                        "id": b.id,
                        "name": b.name,
                        "author": b.author,
                        "public_date": p_date,
                        "rating": b.rating,
                        "genres": [g.name for g in b.genres],
                        "summary": b.summary or "",
                        "cover_pic": encode_cover(b.cover_path),
                        "file_path": b.file_path
                    })
                except Exception as e:
                    print(f"Ошибка при обработке книги {getattr(b, 'id', 'unknown')}: {e}")
                    # Проблемную книгу пропускаем, отдаем следующие
                    continue

        return json.dumps({
            "status": "success",
            "action": "books",
            "data": result
        }, ensure_ascii=False)

    # Если упала база или весь процесс
    except Exception as e:
        print(f"[Критическая ошибка сервера] {e}")
        return json.dumps({
            "status": "error",
            "message": "Ошибка на стороне сервера при получении списка книг"
        }, ensure_ascii=False)


def fetch_genres_json() -> str:
    """Формирование JSON для передачи информации о всех жанрах для фильтров"""

    try:
        with SessionLocal() as session:
            genres = get_genres(session)

            result = [
                {"id": genre.id, "name": genre.name}
                for genre in genres
            ]

        return json.dumps({
            "status": "success",
            "action": "genres",
            "data": result
        }, ensure_ascii=False)

    except Exception as e:
        print(f"[Критическая ошибка сервера] {e}")
        return json.dumps({
            "status": "error",
            "message": "Ошибка на стороне сервера при получении списка жанров"
        }, ensure_ascii=False)


def encode_cover(path: str | None) -> str | None:
    """Перевод изображения в строку для обложки в карточку"""
    if not path:
        return None

    full_path = os.path.join(COVERS_DIR, path)
    if not os.path.exists(full_path):
        return None

    with open(full_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def recv_exact(sock: socket.socket, msg_len: int) -> bytes | None:
    """Получает точное число байт из сокета"""
    buffer = bytearray()
    while len(buffer) < msg_len:
        chunk = sock.recv(msg_len - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return bytes(buffer)



def handle_client(client: socket.socket, address):
    """Цикл работы с клиентом"""
    print(f"[+] Подключился новый клиент: {address}")

    session_role = "guest"
    session_username = None

    with client:
        while True:
            try:
                raw_len = recv_exact(client, 4)
                if not raw_len:
                    break

                message_len = int.from_bytes(raw_len, "big")
                raw_data = recv_exact(client, message_len)
                if not raw_data:
                    break

                # Все входящие сообщения — JSON
                try:
                    data = json.loads(raw_data.decode())
                except (UnicodeDecodeError, json.JSONDecodeError):
                    err = json.dumps({"status": "error", "message": "Неверный формат запроса"})
                    client.sendall(len(err.encode()).to_bytes(4, "big") + err.encode())
                    continue

                action = data.get("action", "")
                print(f"[{address} ({session_username or 'Гость'})] action={action!r}")

                # Глобальная проверка прав администратора
                if action in ADMIN_ONLY_COMMANDS and session_role != "admin":
                    response = json.dumps({
                        "status": "error",
                        "message": "Отказано в доступе: требуются права администратора"
                    }, ensure_ascii=False)

                # --- Публичные команды ----------------------------
                elif action == "get_books":
                    response = fetch_books_json()

                elif action == "get_genres":
                    response = fetch_genres_json()

                elif action == "download":
                    response = fetch_file_json(data.get("file_path", ""))

                elif action == "login":
                    username = data.get("username", "")
                    password = data.get("password", "")
                    with SessionLocal() as session:
                        user = authenticate_user(session, username, password)
                        if user:
                            session_role = user.role.value if hasattr(user.role, "value") else str(user.role)
                            session_username = user.username
                            response = json.dumps({
                                "status": "success",
                                "action": "login",
                                "user_data": {
                                    "username": user.username,
                                    "role": session_role,
                                }
                            }, ensure_ascii=False)
                        else:
                            response = json.dumps({
                                "status": "error",
                                "action": "login",
                                "message": "Неверное имя пользователя или пароль"
                            }, ensure_ascii=False)

                elif action == "register":
                    username = data.get("username", "")
                    password = data.get("password", "")
                    with SessionLocal() as session:
                        success, result = register_user(session, username, password)
                        if success:
                            session_role = result.role.value if hasattr(result.role, "value") else str(result.role)
                            session_username = result.username
                            response = json.dumps({
                                "status": "success",
                                "action": "login",
                                "user_data": {
                                    "username": result.username,
                                    "role": session_role,
                                }
                            }, ensure_ascii=False)
                        else:
                            response = json.dumps({
                                "status": "error",
                                "action": "login",
                                "message": result
                            }, ensure_ascii=False)

                # --- Команды администратора ----------------------
                elif action == "add_genre":
                    with SessionLocal() as session:
                        add_genre(session, data.get("name", ""))
                    response = fetch_genres_json()

                elif action == "delete_genres":
                    ids = [int(i) for i in data.get("ids", [])]
                    with SessionLocal() as session:
                        delete_genres(session, ids)
                    response = fetch_genres_json()

                elif action == "add_book":
                    try:
                        book_filename = data["book_filename"]
                        with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
                            f.write(base64.b64decode(data["book_data"]))

                        cover_filename = None
                        if data.get("cover_data") and data.get("cover_filename"):
                            cover_filename = data["cover_filename"]
                            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                                f.write(base64.b64decode(data["cover_data"]))

                        with SessionLocal() as session:
                            genres = [get_genre(session, gid) for gid in data.get("genre_ids", [])]
                            book = BookTable(
                                name=data["name"],
                                author=data["author"],
                                summary=data["summary"],
                                rating=data["rating"],
                                public_date=datetime.strptime(data["public_date"], "%d.%m.%Y").date(),
                                genres=[g for g in genres if g],
                                file_path=book_filename,
                                cover_path=cover_filename,
                            )
                            add_book(session, book)
                        response = fetch_books_json()
                    except Exception as e:
                        print(f"[Ошибка добавления книги] {e}")
                        response = json.dumps({"status": "error", "message": f"Ошибка при добавлении книги: {e}"},
                                              ensure_ascii=False)

                elif action == "delete_book":
                    book_id = int(data.get("id", 0))
                    with SessionLocal() as session:
                        success = delete_book(session, book_id)
                    response = fetch_books_json() if success else json.dumps(
                        {"status": "error", "message": "Книга не найдена"}, ensure_ascii=False)

                elif action == "edit_book":
                    try:
                        book_filename = None
                        if data.get("book_data") and data.get("book_filename"):
                            book_filename = data["book_filename"]
                            with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
                                f.write(base64.b64decode(data["book_data"]))

                        cover_filename = None
                        if data.get("cover_data") and data.get("cover_filename"):
                            cover_filename = data["cover_filename"]
                            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                                f.write(base64.b64decode(data["cover_data"]))

                        with SessionLocal() as session:
                            success = update_book(session, data, book_filename, cover_filename)
                        response = fetch_books_json() if success else json.dumps(
                            {"status": "error", "message": "Книга не найдена"}, ensure_ascii=False)
                    except Exception as e:
                        print(f"[Ошибка изменения книги] {e}")
                        response = json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

                else:
                    response = json.dumps({"status": "error", "message": f"Неизвестная команда: {action!r}"},
                                          ensure_ascii=False)

                encoded = response.encode()
                client.sendall(len(encoded).to_bytes(4, "big") + encoded)

            except OSError as e:
                print(f"[{address}] Разрыв соединения: {e}")
                break

    print(f"[-] Отключился: {address}")


def start_server():
    init_db()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen()
        print(f"Сервер запущен на {SERVER_HOST}:{SERVER_PORT}")

        while True:
            client, addr = server.accept()
            client_thread = Thread(target=handle_client, args=(client, addr), daemon=True)
            client_thread.start()


if __name__ == "__main__":
    start_server()