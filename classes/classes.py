from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal

from windows.bookCardWidget import Ui_BookCardWidget


class BookCard(QWidget):
    # Вызывает сокет для отправки запроса на скачивание
    download_requested = pyqtSignal(str)

    def __init__(self, name: str, author: str, public_date,
                 rating: float, genres: list[str], summary: str, pixmap: QPixmap, file_path: str):
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

        self.file_path = file_path
        self.ui.download_label.linkActivated.connect(lambda: self.download_requested.emit(self.file_path))
