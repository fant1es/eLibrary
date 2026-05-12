from PyQt6 import QtWidgets
import windows.loginWindow as loginWindow


class Login(QtWidgets.QMainWindow, loginWindow.Ui_MainWindow):
    def __init__(self, socket_worker):
        super().__init__()
        self.setupUi(self)
        self.socket_worker = socket_worker

        with open("styles/loginStyle.qss", "r", encoding="utf-8") as file:
            self.setStyleSheet(file.read())

        self.login_btn.clicked.connect(self.try_login)
        self.register_btn.clicked.connect(self.try_register)

    def try_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        self.socket_worker.send_json({"action": "login", "username": username, "password": password})

    def try_register(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        self.socket_worker.send_json({"action": "register", "username": username, "password": password})