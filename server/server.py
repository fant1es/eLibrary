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

# Список команд, требующих прав администратора
ADMIN_ONLY_COMMANDS = [
    "add_genre",
    "delete_genres",
    "add_book",
    "delete_book",
    "edit_book"
]


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

    # Будем хранить роль и имя пользователя для проверки уровня доступа
    session_role = "guest"
    session_username = None

    with client:
        while True:
            try:
                # Читаем 4 байта как длину следующего сообщения от клиента
                raw_len = recv_exact(client, 4)
                if not raw_len:
                    break

                message_len = int.from_bytes(raw_len, "big")

                # Читаем саму команду
                raw_data = recv_exact(client, message_len)
                if not raw_data:
                    break

                message = raw_data.decode().strip()

                # Извлекаем тип действия, желаемый пользователем
                action = message.split('|')[0] if '|' in message else message

                print(f"[{address} ({session_username or 'Гость'})] Получено: {message[:50]}")

                # Глобальная проверка прав
                if action in ADMIN_ONLY_COMMANDS and session_role != "admin":
                    response = json.dumps({
                        "status": "error",
                        "message": "Отказано в доступе: требуются права администратора"
                    }, ensure_ascii=False)

                # --- Публичные команды --------
                elif message == "get_books":
                    response = fetch_books_json()
                elif message == "get_genres":
                    response = fetch_genres_json()

                elif message.startswith("download|"):
                    file_path = message.split("|", 1)[1].strip()
                    response = fetch_file_json(file_path)

                elif message.startswith("login|"):
                    try:
                        # Ожидаем формат "login|username:password"
                        credentials = message.split("|", 1)[1].strip()
                        username, password = credentials.split(":", 1)

                        with SessionLocal() as session:
                            # Проверяем через БД
                            user = authenticate_user(session, username, password)

                            if user:
                                # Запоминаем пользователя
                                session_role = user.role.value if hasattr(user.role, "value") else str(user.role)
                                session_username = user.username

                                response = json.dumps({
                                    "status": "success",
                                    "action": "login",
                                    "user_data": {
                                        "username": user.username,
                                        "role": user.role.value if hasattr(user.role, "value") else str(user.role)
                                    }
                                }, ensure_ascii=False)
                            else:
                                response = json.dumps({
                                    "status": "error",
                                    "action": "login",
                                    "message": "Неверное имя пользователя или пароль"
                                }, ensure_ascii=False)
                    except ValueError:
                        response = json.dumps({"status": "error", "message": "Неверный формат данных авторизации"})

                elif message.startswith("register|"):
                    try:
                        credentials = message.split("|", 1)[1].strip()
                        username, password = credentials.split(":", 1)

                        with SessionLocal() as session:
                            # Функция register_user должна быть реализована в crud.py
                            # Возвращает кортеж: (Успех: bool, Объект пользователя или текст ошибки)
                            success, result = register_user(session, username, password)

                            if success:
                                # Запоминаем пользователя
                                session_role = result.role.value if hasattr(result.role, "value") else str(result.role)
                                session_username = result.username

                                response = json.dumps({
                                    "status": "success",
                                    "action": "login",  # Отправляем как login, чтобы клиент сразу вошел
                                    "user_data": {
                                        "username": result.username,
                                        "role": result.role.value if hasattr(result.role, "value") else str(result.role)
                                    }
                                }, ensure_ascii=False)
                            else:
                                response = json.dumps({
                                    "status": "error",
                                    "action": "login",
                                    "message": result  # Текст ошибки, например "Имя уже занято"
                                }, ensure_ascii=False)
                    except ValueError:
                        response = json.dumps({"status": "error", "message": "Неверный формат данных регистрации"})

                # --- Команды администратора ---
                elif message.startswith("add_genre|"):
                    genre_name = message.split("|", 1)[1]
                    with SessionLocal() as session:
                        add_genre(session, genre_name)
                    response = fetch_genres_json()

                elif message.startswith("delete_genres|"):
                    genre_ids = [int(gid) for gid in message.split("|", 1)[1].split(",")]
                    with SessionLocal() as session:
                        delete_genres(session, genre_ids)
                    response = fetch_genres_json()

                elif message.startswith("add_book|"):
                    try:
                        payload = json.loads(message.split("|", 1)[1])

                        # Сохраняем файл книги
                        book_filename = payload["book_filename"]
                        with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
                            f.write(base64.b64decode(payload["book_data"]))

                        # Сохраняем обложку (опционально)
                        cover_filename = None
                        if payload.get("cover_data") and payload.get("cover_filename"):
                            cover_filename = payload["cover_filename"]
                            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                                f.write(base64.b64decode(payload["cover_data"]))

                        # Добавляем книгу в базу данных
                        with SessionLocal() as session:
                            genres = [get_genre(session, gid) for gid in payload.get("genre_ids", [])]
                            genres = [g for g in genres if g]

                            book = BookTable(
                                name=payload["name"],
                                author=payload["author"],
                                summary=payload["summary"],
                                rating=payload["rating"],
                                public_date=datetime.strptime(payload["public_date"], "%d.%m.%Y").date(),
                                genres=genres,
                                file_path=book_filename,
                                cover_path=cover_filename,
                            )
                            add_book(session, book)

                        response = fetch_books_json()

                    except Exception as e:
                        print(f"[Ошибка добавления книги] {e}")
                        response = json.dumps({"status": "error", "message": f"Ошибка при добавлении книги: {e}"},
                                              ensure_ascii=False)

                elif message.startswith("delete_book|"):
                    book_id = int(message.split("|", 1)[1])
                    with SessionLocal() as session:
                        # Удаляем и проверяем, что действительно удалили внутри метода
                        success = delete_book(session, book_id)

                    if success:
                        response = fetch_books_json()
                    else:
                        response = json.dumps({"status": "error", "message": "Книга не найдена"},
                                              ensure_ascii=False)

                elif message.startswith("edit_book|"):
                    try:
                        payload = json.loads(message.split("|", 1)[1])

                        book_filename = None
                        if payload.get("book_data") and payload.get("book_filename"):
                            book_filename = payload["book_filename"]
                            with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
                                f.write(base64.b64decode(payload["book_data"]))

                        cover_filename = None
                        if payload.get("cover_data") and payload.get("cover_filename"):
                            cover_filename = payload["cover_filename"]
                            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                                f.write(base64.b64decode(payload["cover_data"]))

                        with SessionLocal() as session:
                            success = update_book(session, payload, book_filename, cover_filename)

                        response = fetch_books_json() if success else json.dumps(
                            {"status": "error", "message": "Книга не найдена"}, ensure_ascii=False)

                    except Exception as e:
                        print(f"[Ошибка изменения] {e}")
                        response = json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

                else:
                    response = json.dumps({"status": "error", "message": "unknown command"})

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
