import json
import os
import socket
import base64

from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

load_dotenv()


class SocketWorker(QThread):
    """Сокет клиента для посылания запросов серверу"""

    # Сигналы для вызова методов в UI (вызывать напрямую из потока методы нельзя)
    connected = pyqtSignal()
    disconnected = pyqtSignal()

    books_received = pyqtSignal(list)
    genres_received = pyqtSignal(list)
    file_received = pyqtSignal(str, bytes)

    error_occurred = pyqtSignal(str)

    HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    PORT = int(os.getenv("SERVER_PORT", 8080))

    def __init__(self):
        super().__init__()
        self._socket: socket.socket | None = None
        self._running = False

    def run(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.HOST, self.PORT))
            self._running = True
            self.connected.emit()

            while self._running:
                # Читаем 4 байта — длина следующего сообщения
                raw_len = self._recv_exact(4)
                if not raw_len:
                    break
                message_len = int.from_bytes(raw_len, "big")

                raw_data = self._recv_exact(message_len)
                if not raw_data:
                    break

                # Должны получить JSON
                try:
                    json_data = json.loads(raw_data.decode())
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

                # Проверка статуса и типа ответа
                if isinstance(json_data, dict):
                    status = json_data.get("status")
                    if status == "error":
                        self.error_occurred.emit(json_data["message"])

                    elif status == "success":
                        action = json_data.get("action", "books")
                        if action == "books":
                            self.books_received.emit(json_data.get("data", []))
                        elif action == "genres":
                            self.genres_received.emit(json_data.get("data", []))
                        elif action == "download":
                            filename = json_data["filename"]
                            file_bytes = base64.b64decode(json_data["file_data"])
                            self.file_received.emit(filename, file_bytes)

        except ConnectionRefusedError:
            self.error_occurred.emit("Сервер недоступен")
        except OSError:
            # Здесь неожиданный обрыв, а не наш stop()
            if self._running:
                self.error_occurred.emit("Потеряно соединение с сервером")
        finally:
            self._running = False
            self.disconnected.emit()

    def request_download(self, file_path: str):
        """Вызывается при нажатии на "Скачать книгу" из карточки"""
        self.send(f"download|{file_path}")

    def _recv_exact(self, msg_len: int) -> bytes | None:
        """Получает точное число байт"""
        buffer = bytearray()

        while len(buffer) < msg_len:
            chunk = self._socket.recv(msg_len - len(buffer))
            if not chunk:
                return None
            buffer += chunk

        return bytes(buffer)

    def send(self, message: str):
        """Вспомогательный метод для отправки данных сокетом"""
        if self._socket and self._running:
            try:
                encoded = message.encode()
                # Сначала отправляем 4 байта длины, затем само сообщение
                self._socket.sendall(len(encoded).to_bytes(4, "big") + encoded)
            except OSError as e:
                self.error_occurred.emit(str(e))

    def stop(self):
        self._running = False
        if self._socket:
            self._socket.close()
