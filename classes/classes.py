from datetime import datetime

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap

from windows.bookCardWidget import Ui_BookCardWidget
from database.database import BookTable


class Book:
    def __init__(self, name: str, author: str, summary: str,
                 public_date: datetime, cover_path: str, id: int = None):
        self.id = id
        self.name = name
        self.author = author
        self.summary = summary
        self.public_date = public_date
        self.cover_path = cover_path

    def __str__(self):
        date = self.public_date.strftime("%d.%m.%Y")
        return (f"Книга #{self.id}: {self.name}, Автор: {self.author},"
                f" Дата издания: {date}")


class BookCard(QWidget):
    def __init__(self, book: BookTable):
        super().__init__()
        self.ui = Ui_BookCardWidget()
        self.ui.setupUi(self)

        # Для подсветки и наличия границы у карточки
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)

        self.book = book

        pixmap = QPixmap(self.book.cover_path)
        self.ui.picture_label.setPixmap(pixmap)
        self.ui.name_label.setText(self.book.name)
        self.ui.author_label.setText(self.book.author)
        self.ui.summary_label.setText(self.book.summary)
        self.ui.date_label.setText("Дата издания: " + self.book.public_date.strftime("%d.%m.%Y"))
        self.ui.download_label.setText(
            '<a href="download" style="color: #4CAF50; font-size: 14px; text-decoration: underline;">Скачать книгу</a>')
