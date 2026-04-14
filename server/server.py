import base64
import json
import os
import socket
from threading import Thread

from dotenv import load_dotenv

from database.crud import get_books, get_genres, add_genre, delete_genres
from database.database import SessionLocal, init_db

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, os.getenv("COVERS_DIR", "content/covers"))
BOOKS_DIR = os.path.join(BASE_DIR, os.getenv("BOOKS_DIR", "content/books"))


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
    with client:
        while True:
            try:
                # Читаем 4 байта — длина следующего сообщения от клиента
                raw_len = recv_exact(client, 4)
                if not raw_len:
                    break

                message_len = int.from_bytes(raw_len, "big")

                # Читаем саму команду
                raw_data = recv_exact(client, message_len)
                if not raw_data:
                    break

                message = raw_data.decode().strip()
                print(f"[{address}] Получено: {message}")

                # Обработка типа запроса
                if message == "get_books":
                    response = fetch_books_json()
                elif message == "get_genres":
                    response = fetch_genres_json()

                elif message.startswith("download|"):
                    file_path = message.split("|", 1)[1].strip()
                    response = fetch_file_json(file_path)

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
