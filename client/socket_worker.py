import socket, os
from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

load_dotenv()


class SocketWorker(QThread):
    # Сигналы для вызова методов в UI (вызывать напрямую из потока нельзя)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    response_received = pyqtSignal(str)
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
                data = self._socket.recv(1024)
                if not data:
                    break
                self.response_received.emit(data.decode())

        except ConnectionRefusedError:
            self.error_occurred.emit("Сервер недоступен")
        # Когда сокет закрывается через stop()
        except OSError:
            pass
        finally:
            self._running = False
            self.disconnected.emit()

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
