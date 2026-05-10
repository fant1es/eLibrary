import sys
from PyQt6.QtWidgets import QApplication
from client.client_main import Client
from client.login_client import Login
from client.socket_worker import SocketWorker


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.socket_worker = SocketWorker()
        self.socket_worker.start()

        self.socket_worker.error_occurred.connect(self.show_error_message) # Добавляем связь

        # Сначала окно с логином, главное после входа
        self.login_window = Login(self.socket_worker)
        self.main_window = None

        self.socket_worker.login_result.connect(self.handle_login)

        self.login_window.show()

    def show_error_message(self, message):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self.login_window, "Ошибка", message)

    def handle_login(self, success, user_data):
        if success:
            print(f"Авторизация успешна! Данные: {user_data}")
            self.login_window.hide()

            # Теперь даем главное окно юзеру
            self.main_window = Client(self.socket_worker)
            self.main_window.show()
        else:
            # Окно логина само покажет ошибку через error_occurred
            print("Вход или регистрация не удались")

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()