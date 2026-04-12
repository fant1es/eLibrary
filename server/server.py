import os, json
from dotenv import load_dotenv
import socket
from threading import Thread

from database.database import SessionLocal, init_db
from database.crud import get_books

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))


def fetch_books_json() -> str:
    with SessionLocal() as session:
        books = get_books(session)
        result = [
            {
                "id": b.id, "name": b.name, "author": b.author,
                "summary": b.summary, "rating": b.rating,
                "cover_path": b.cover_path,
                "public_date": b.public_date.strftime("%d.%m.%Y"),
                "genres": [g.name for g in b.genres],
            }
            for b in books
        ]
        return json.dumps(result, ensure_ascii=False)


def handle_client(client, address):
    print(f"[+] Подключился новый клиент: {address}")
    with client:
        while True:
            try:
                data = client.recv(4096)
                if not data:
                    break

                message = data.decode()
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
