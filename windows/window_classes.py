from windows import addBookWidget
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog


class AddBookWin(QtWidgets.QWidget, addBookWidget.Ui_addBookWidget):
    # Сигналы для связи с основным классом
    genre_add_requested = QtCore.pyqtSignal(str)
    genre_delete_requested = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowTitleHint)

        self.add_genre_btn.clicked.connect(self._on_add_genre)
        self.add_genre_edit.returnPressed.connect(self._on_add_genre)
        self.del_genres_brn.clicked.connect(self._on_delete_genres)

        self.cancel_btn.clicked.connect(self.cancel)

        self.review_cover_path_btn.clicked.connect(self.select_cover_path)
        self.review_book_path_btn.clicked.connect(self.select_book_path)

        self.genres_list_widget.installEventFilter(self)

    def set_genres(self, genres: list[dict]):
        """Заполняет список жанров, очищая старые данные"""
        self.genres_list_widget.clear()
        for genre in genres:
            # Используем и имя, и ID
            item = QtWidgets.QListWidgetItem(genre["name"])
            # Сохраняем ID в объекте элемента, чтобы потом легко его достать
            item.setData(QtCore.Qt.ItemDataRole.UserRole, genre["id"])
            self.genres_list_widget.addItem(item)

    def _on_add_genre(self):
        """Вызов сигнала на добавление жанра"""
        name = self.add_genre_edit.text().strip()
        if name:
            self.genre_add_requested.emit(name)
            self.add_genre_edit.clear()

    def _on_delete_genres(self):
        """Вызов сигнала на удаление жанров"""
        selected_items = self.genres_list_widget.selectedItems()
        if not selected_items:
            return

        # Получаем список ID всех выбранных элементов
        ids_to_delete = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected_items]

        # Подтверждение действия
        res = QtWidgets.QMessageBox.question(
            self, "Удаление", f"Удалить выбранные жанры ({len(selected_items)} шт.)?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if res == QtWidgets.QMessageBox.StandardButton.Yes:
            self.genre_delete_requested.emit(ids_to_delete)

    def eventFilter(self, source, event):
        """Ловим нажатие Delete на списке жанров"""
        if event.type() == QtCore.QEvent.Type.KeyPress and source is self.genres_list_widget:
            if event.key() == QtCore.Qt.Key.Key_Delete:
                self._on_delete_genres()
                return True
        return super().eventFilter(source, event)

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
