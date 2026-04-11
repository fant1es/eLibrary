from datetime import datetime

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout

# from rapidfuzz import process, fuzz

from classes.classes import BookCard
from client.delegates import RangeDelegate
from windows import clientWindow
from database.database import BookTable
from client.socket_worker import SocketWorker


class Client(QtWidgets.QMainWindow, clientWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # --- Установка потока с сокетом -----------------------
        self.socket_worker = SocketWorker()
        self.socket_worker.connected.connect(lambda: print("Успешное подключение!"))
        self.socket_worker.connected.connect(lambda: self.socket_worker.send("ping"))
        self.socket_worker.disconnected.connect(lambda: print("Отключение от сервера."))
        self.socket_worker.response_received.connect(self.on_server_response)

        self.socket_worker.start()

        # --- Установка дерева с фильтрами ---------------------
        self.tree_model = setup_filter_tree()
        self.filter_tree.expandAll()
        self.filter_tree.setModel(self.tree_model)

        self.filter_tree.setIndentation(20)
        self.filter_tree.setAnimated(True)
        self.filter_tree.setAlternatingRowColors(True)
        self.filter_tree.setUniformRowHeights(False)

        self.range_delegate = RangeDelegate()
        self.filter_tree.setItemDelegate(self.range_delegate)

        load_books(self)

        print(self.scrollAreaWidgetContents.children())

        # --- Привязка событий под кнопки и триггеры ------------
        self.exit_btn.clicked.connect(self.exit)
        self.exit_action.triggered.connect(self.exit)

    def on_server_response(self, message: str):
        print(f"Получено сообщение от сервера: {message}")


    def exit(self):
        self.socket_worker.stop()
        self.socket_worker.wait()
        self.close()


def setup_filter_tree():
    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(["Фильтры"])

    # Родители-фильтры с детьми
    filters_children = {"Авторы": [],
                        "Жанры": ["Фэнтези", "Детектив"]
                        }

    for category, options in filters_children.items():
        parent = QStandardItem(category + ":")
        parent.setEditable(False)

        for option in options:
            child = QStandardItem(option)
            child.setCheckable(True)
            parent.appendRow(child)

        model.appendRow(parent)

    # Родитель-фильтр без детей под делегат
    def create_range_item(name, start_val, min_val, max_val, step, decimal):
        item = QStandardItem(f"{name}: {start_val}")
        item.setEditable(True)

        item.setData("range_editor", RangeDelegate.RoleTag)
        item.setData(min_val, RangeDelegate.RoleMin)
        item.setData(max_val, RangeDelegate.RoleMax)
        item.setData(step, RangeDelegate.RoleStep)
        item.setData(decimal, RangeDelegate.RoleDecimals)
        item.setData(name, RangeDelegate.RoleName)

        return item

    model.appendRow(create_range_item("Дата издания", "1800-2026", 1800, 2026, 1, 0))
    model.appendRow(create_range_item("Рейтинг", "1-5 ★", 1, 5, 0.5, 1))

    return model


def load_books(self):
    books_list = [
        BookTable(
            name="Мастер и Маргарита",
            author="Михаил Булгаков",
            summary="Классика о Москве, любви и визите дьявола.",
            public_date=datetime.strptime("15.01.1967", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="1984",
            author="Джордж Оруэлл",
            summary="Культовая антиутопия о тоталитаризме и Большом Брате.",
            public_date=datetime.strptime("08.06.1949", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Чистый код",
            author="Роберт Мартин",
            summary="Руководство по созданию гибкого и понятного программного обеспечения.",
            public_date=datetime.strptime("01.08.2008", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Ведьмак: Последнее желание",
            author="Анджей Сапковский",
            summary="Первая книга о приключениях Геральта из Ривии.",
            public_date=datetime.strptime("20.12.1993", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Алгоритмы: построение и анализ",
            author="Томас Кормен",
            summary="Фундаментальный труд по основам современных алгоритмов.",
            public_date=datetime.strptime("10.04.1990", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Марсианин",
            author="Энди Уир",
            summary="История выживания инженера на красной планете в одиночку.",
            public_date=datetime.strptime("11.02.2011", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Цветы для Элджернона",
            author="Дэниел Киз",
            summary="Трогательная история об эксперименте над человеческим интеллектом.",
            public_date=datetime.strptime("10.03.1959", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Гарри Поттер и философский камень",
            author="Дж.К. Роулинг",
            summary="Начало истории о мальчике, который выжил.",
            public_date=datetime.strptime("26.06.1997", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Идеальный программист",
            author="Роберт Мартин",
            summary="Книга о профессиональном подходе к разработке и ответственности.",
            public_date=datetime.strptime("13.05.2011", "%d.%m.%Y").date(),
            cover_path=""
        ),
        BookTable(
            name="Краткая история времени",
            author="Стивен Хокинг",
            summary="Научно-популярный бестселлер об устройстве Вселенной.",
            public_date=datetime.strptime("01.04.1988", "%d.%m.%Y").date(),
            cover_path=""
        )
    ]

    layout = self.scrollAreaWidgetContents.layout()

    if layout is None:
        layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(layout)

    for book in books_list:
        book_card = BookCard(book)
        layout.addWidget(book_card)
