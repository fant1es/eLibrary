import sys
from PyQt6.QtWidgets import QApplication
from client.client_main import Client


def main():
    # Запускаем обычный PyQt интерфейс
    app = QApplication(sys.argv)

    try:
        with open("styles/style.qss", "r", encoding="utf-8") as file:
            app.setStyleSheet(file.read())
    except FileNotFoundError:
        print("Файл стилей не найден.")

    window = Client()
    window.show()

    # Запускаем стандартный цикл PyQt (он заблокирует поток до закрытия окна)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()