import sys
from PyQt6.QtWidgets import QApplication
from client.client_main import Client
from client.login_client import Login
from client.socket_worker import SocketWorker


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Создаём класс с сокетом, но не запускаем, после первой попытке входа/регистрации
        self.socket_worker = SocketWorker()

        self.login_window = Login(self.socket_worker)
        self.main_window = None

        self.socket_worker.login_result.connect(self.handle_login)

        self.login_window.show()

    def handle_login(self, success, user_data):
        if success:
            print(f"Авторизация успешна! Роль: {user_data.get('role')}")
            self.login_window.hide()

            user_role = user_data.get('role', 'user')
            self.main_window = Client(self.socket_worker, user_role)
            self.main_window.show()
        else:
            print("Вход или регистрация не удались")

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()