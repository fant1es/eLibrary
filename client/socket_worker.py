import json
import socket, os
from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

load_dotenv()


class SocketWorker(QThread):
    # Сигналы для вызова методов в UI (вызывать напрямую из потока нельзя)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    books_received = pyqtSignal(list)
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

                json_data = json.loads(raw_data.decode())
                # Точная проверка после выгрузки json на список
                if isinstance(json_data, list):
                    self.books_received.emit(json_data)

        except ConnectionRefusedError:
            self.error_occurred.emit("Сервер недоступен")
        # Когда сокет закрывается через stop()
        except OSError:
            pass
        finally:
            self._running = False
            self.disconnected.emit()

    def _recv_exact(self, msg_len: int) -> bytes | None:
        buffer = bytearray()
        while len(buffer) < msg_len:
            chunk = self._socket.recv(msg_len - len(buffer))
            if not chunk:
                return None
            buffer += chunk
        return bytes(buffer)

    def send(self, message: str):
        if self._socket and self._running:
            try:
                self._socket.sendall(message.encode())
            except OSError as e:
                self.error_occurred.emit(str(e))

    def stop(self):
        self._running = False
        if self._socket:
            self._socket.close()
