
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout
from datetime import datetime
from classes.classes import Book, BookCard

from windows import clientWindow
from client.delegates import RangeDelegate
from rapidfuzz import process, fuzz


class Client(QtWidgets.QMainWindow, clientWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

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


    def exit(self):
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
    books = [
        Book("Мастер и Маргарита", "Михаил Булгаков", "Классика о Москве, любви и визите дьявола.",
             datetime.strptime("15.01.1967", "%d.%m.%Y"), ""),
        Book("1984", "Джордж Оруэлл", "Культовая антиутопия о тоталитаризме и Большом Брате.",
             datetime.strptime("08.06.1949", "%d.%m.%Y"), ""),
        Book("Чистый код", "Роберт Мартин", "Руководство по созданию гибкого и понятного программного обеспечения.",
             datetime.strptime("01.08.2008", "%d.%m.%Y"), ""),
        Book("Ведьмак: Последнее желание", "Анджей Сапковский", "Первая книга о приключениях Геральта из Ривии.",
             datetime.strptime("20.12.1993", "%d.%m.%Y"), ""),
        Book("Алгоритмы: построение и анализ", "Томас Кормен",
             "Фундаментальный труд по основам современных алгоритмов.",
             datetime.strptime("10.04.1990", "%d.%m.%Y"), ""),
        Book("Марсианин", "Энди Уир", "История выживания инженера на красной планете в одиночку.",
             datetime.strptime("11.02.2011", "%d.%m.%Y"), ""),
        Book("Цветы для Элджернона", "Дэниел Киз", "Трогательная история об эксперименте над человеческим интеллектом.",
             datetime.strptime("10.03.1959", "%d.%m.%Y"), ""),
        Book("Гарри Поттер и философский камень", "Дж.К. Роулинг", "Начало истории о мальчике, который выжил.",
             datetime.strptime("26.06.1997", "%d.%m.%Y"), ""),
        Book("Идеальный программист", "Роберт Мартин",
             "Книга о профессиональном подходе к разработке и ответственности.",
             datetime.strptime("13.05.2011", "%d.%m.%Y"), ""),
        Book("Краткая история времени", "Стивен Хокинг", "Научно-популярный бестселлер об устройстве Вселенной.",
             datetime.strptime("01.04.1988", "%d.%m.%Y"), "")
    ]

    layout = self.scrollAreaWidgetContents.layout()

    if layout is None:
        layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaWidgetContents.setLayout(layout)

    for book in books:
        book_card = BookCard(book)
        layout.addWidget(book_card)
