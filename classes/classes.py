from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap

from windows.bookCardWidget import Ui_BookCardWidget
from database.database import BookTable


class BookCard(QWidget):
    def __init__(self, name: str, author: str, public_date,
                 rating: float, genres: list[str], summary: str, pixmap: QPixmap):
        super().__init__()
        self.ui = Ui_BookCardWidget()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)

        self.ui.picture_label.setPixmap(pixmap)
        self.ui.name_label.setText(name)
        self.ui.author_label.setText(author)
        self.ui.summary_label.setText(summary)
        self.ui.date_label.setText("Дата издания: " + public_date.strftime("%d.%m.%Y"))
        self.ui.download_label.setText(
            '<a href="download" style="color: #4CAF50; font-size: 14px; text-decoration: underline;">Скачать книгу</a>')
