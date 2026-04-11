import os
from dotenv import load_dotenv

import socket
from threading import Thread

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))


def handle_client(client, address):
    print(f"[+] Подключился новый клиент: {address}")
    with client:
        while True:
            try:
                data = client.recv(1024)
                if not data:
                    break
                message = data.decode()
                print(f"[{address}] Получено: {message}")

                if message == "ping":
                    client.sendall(b"pong")
                else:
                    client.sendall(b"unknown command")

            except OSError as e:
                print(f"[{address}] Разрыв соединения: {e}")
                break

    print(f"[-] Отключился: {address}")


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen()
        print(f"Сервер запущен на {SERVER_HOST}:{SERVER_PORT}")

        while True:
            client, addr = server.accept()
            print("good")
            client_thread = Thread(target=handle_client, args=(client, addr), daemon=True)
            client_thread.start()


if __name__ == "__main__":
    start_server()
