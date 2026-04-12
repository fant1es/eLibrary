from datetime import datetime
import base64
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import QByteArray

# from rapidfuzz import process, fuzz

from classes.classes import BookCard
from client.delegates import RangeDelegate
from windows import clientWindow
from client.socket_worker import SocketWorker


class Client(QtWidgets.QMainWindow, clientWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # --- Установка потока с сокетом -----------------------
        self.socket_worker = SocketWorker()
        self.socket_worker.connected.connect(lambda: print("Успешное подключение!"))
        self.socket_worker.connected.connect(lambda: self.socket_worker.send("get_books"))
        self.socket_worker.disconnected.connect(lambda: print("Отключение от сервера."))
        self.socket_worker.books_received.connect(self.on_books_received)

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

        print(self.scrollAreaWidgetContents.children())

        # --- Привязка событий под кнопки и триггеры ------------
        self.exit_btn.clicked.connect(self.exit)
        self.exit_action.triggered.connect(self.exit)

    def on_books_received(self, books: list[dict]):
        layout = self.scrollAreaWidgetContents.layout() or QVBoxLayout(self.scrollAreaWidgetContents)

        for book in books:
            cover_b64 = book.get("cover_pic")
            if cover_b64:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(base64.b64decode(cover_b64)))
                print('check')
            else:
                pixmap = QPixmap()  # заглушка
                print("bad")

            book_card = BookCard(
                name=book["name"],
                author=book["author"],
                public_date=datetime.strptime(book["public_date"], "%d.%m.%Y").date(),
                rating=book["rating"],
                genres=book["genres"],
                summary=book["summary"],
                pixmap=pixmap,
            )
            layout.addWidget(book_card)


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
