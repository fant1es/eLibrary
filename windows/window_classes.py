from windows import addBookWidget
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog


class AddBookWin(QtWidgets.QWidget, addBookWidget.Ui_addBookWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowTitleHint)

        self.review_cover_path_btn.clicked.connect(self.select_cover_path)
        self.review_book_path_btn.clicked.connect(self.select_book_path)
        self.cancel_btn.clicked.connect(self.cancel)

    def select_cover_path(self):
        cover_path, _ = QFileDialog.getOpenFileName(
            None,
            "Выберите обложку книги",
            "",
            "Images (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if cover_path:
            self.cover_path_edit.setText(cover_path)

    def select_book_path(self):
        book_path, _ = QFileDialog.getOpenFileName(
            None,
            "Выберите файл книги",
            "",
            "E-books (*.pdf *.epub *.fb2);;Text Files (*.txt);;All Files (*)"
        )
        if book_path:
            self.book_path_edit.setText(book_path)

    def cancel(self):
        self.hide()
