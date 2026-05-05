from PyQt6 import QtWidgets
import windows.loginWindow as loginWindow


class Login(QtWidgets.QMainWindow, loginWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        with open("styles/loginStyle.qss", "r", encoding="utf-8") as file:
            self.setStyleSheet(file.read())