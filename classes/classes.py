from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from datetime import datetime
from windows.bookCardWidget import Ui_BookCardWidget
from PyQt6.QtGui import QPixmap


class Book:
    def __init__(self, name: str, author: str, summary: str,
                 public_date: datetime, cover_path: str):
        self.name = name
        self.author = author
        self.summary = summary
        self.public_date = public_date
        self.cover_path = cover_path

    def __str__(self):
        date = self.public_date.strftime("%d.%m.%Y")
        return (f"Книга: {self.name}, Автор: {self.author},"
                f" Дата издания: {date}")


class BookCard(QWidget):
    def __init__(self, book: Book):
        super().__init__()
        self.ui = Ui_BookCardWidget()
        self.ui.setupUi(self)

        # Для подсветки и наличия границы у карточки
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)

        self._book = book

        pixmap = QPixmap(self._book.cover_path)
        self.ui.picture_label.setPixmap(pixmap)
        self.ui.name_label.setText(self._book.name)
        self.ui.author_label.setText(self._book.author)
        self.ui.summary_label.setText(self._book.summary)
        self.ui.date_label.setText("Дата издания: " + self._book.public_date.strftime("%d.%m.%Y"))
        self.ui.download_label.setText(
            '<a href="download" style="color: #4CAF50; font-size: 14px; text-decoration: underline;">Скачать книгу</a>')
