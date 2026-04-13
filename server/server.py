import base64
import json
import os
import socket
from threading import Thread

from dotenv import load_dotenv

from database.crud import get_books
from database.database import SessionLocal, init_db

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, os.getenv("COVERS_DIR", "covers"))


def fetch_books_json() -> str:
    try:
        with SessionLocal() as session:
            books = get_books(session)
            result = []
            for b in books:
                try:
                    # Формируем дату безопасно
                    p_date = b.public_date.strftime("%d.%m.%Y") if b.public_date else "Дата неизвестна"

                    result.append({
                        "name": b.name,
                        "author": b.author,
                        "public_date": p_date,
                        "rating": b.rating,
                        "genres": [g.name for g in b.genres],
                        # Возможный NULL в книге
                        "summary": b.summary or "",
                        "cover_pic": encode_cover(b.cover_path),
                    })
                except Exception as e:
                    print(f"Ошибка при обработке книги {getattr(b, 'id', 'unknown')}: {e}")
                    # Проблемную книгу пропускаем, отдаем следующие
                    continue

        return json.dumps({
            "status": "success",
            "data": result
        }, ensure_ascii=False)

    # Если упала база или весь процесс
    except Exception as e:
        print(f"[Критическая ошибка сервера] {e}")
        return json.dumps({
            "status": "error",
            "message": "Ошибка на стороне сервера при получении списка книг"
        }, ensure_ascii=False)


# Перевод изображения в строку для обложки в карточку
def encode_cover(path: str | None) -> str | None:
    if not path:
        return None
    full_path = os.path.join(COVERS_DIR, path)
    if not os.path.exists(full_path):
        return None

    with open(full_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def handle_client(client, address):
    print(f"[+] Подключился новый клиент: {address}")
    with client:
        while True:
            try:
                data = client.recv(4096)
                if not data:
                    break

                message = data.decode().strip()
                print(f"[{address}] Получено: {message}")

                if message == "get_books":
                    books_json = fetch_books_json()
                    # Отправляем длину сообщения перед данными
                    encoded = books_json.encode()
                    client.sendall(len(encoded).to_bytes(4, "big") + encoded)
                else:
                    encoded = b"unknown command"
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
