import sys
from PyQt6.QtWidgets import QApplication
from client import client_main

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        with open("styles/style.qss", "r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())
    except FileNotFoundError:
        print("Файл стилей не найден, загружен стандартный вид.")

    window = client_main.Client()
    window.show()

    app.exec()
    