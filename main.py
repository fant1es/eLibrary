import sys
from PyQt6.QtWidgets import QApplication
from client.client_main import Client
from client.login_client import Login
from client.socket_worker import SocketWorker


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.load_styles()

        # Инициализируем сокет ОДИН раз
        self.socket_worker = SocketWorker()
        self.socket_worker.start()

        self.login_window = Login(self.socket_worker)

        self.socket_worker.connected.connect(lambda: print("Сессия сокета активна"))

        self.login_window.show()

    def load_styles(self):
        try:
            with open("styles/style.qss", "r", encoding="utf-8") as file:
                self.app.setStyleSheet(file.read())
        except FileNotFoundError:
            print("Файл стилей не найден.")

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()