import os
import base64
import json
from datetime import datetime

from windows import addBookWidget
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QPixmap


class AddBookWin(QtWidgets.QWidget, addBookWidget.Ui_addBookWidget):
    # Сигналы для связи с основным классом
    genre_add_requested = QtCore.pyqtSignal(str)
    genre_delete_requested = QtCore.pyqtSignal(list)
    book_add_requested = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowTitleHint)

        self.add_genre_btn.clicked.connect(self._on_add_genre)
        self.add_genre_edit.returnPressed.connect(self._on_add_genre)
        self.del_genres_brn.clicked.connect(self._on_delete_genres)

        self.add_btn.clicked.connect(self._on_add_book)
        self.cancel_btn.clicked.connect(self.cancel)

        self.review_cover_path_btn.clicked.connect(self.select_cover_path)
        self.review_book_path_btn.clicked.connect(self.select_book_path)

        self.genres_list_widget.installEventFilter(self)

    # --- Жанры -------------------------------------------------
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

    # --- Добавление книги --------------------------------------
    @staticmethod
    def _cap_if_not_digit(text: str) -> str:
        """Первая буква заглавная, если строка не начинается с цифры"""
        if not text:
            return text
        return text if text[0].isdigit() else text[0].upper() + text[1:]

    def _get_validated_data(self) -> dict | None:
        """Проверка и возврат всех данных"""
        # Смотрим все ошибки и если есть выводим все
        errors = []

        # Название
        name = self.book_name_edit.text().strip()
        if not name:
            errors.append("Название книги не может быть пустым")
        else:
            name = self._cap_if_not_digit(name)

        # Автор — каждое слово с заглавной
        author = self.author_edit.text().strip()
        if not author:
            errors.append("Имя автора не может быть пустым")
        else:
            author = " ".join(word.capitalize() for word in author.split())

        # Описание
        summary = self.summary_text_edit.toPlainText().strip()
        summary = self._cap_if_not_digit(summary) if summary else ""

        # Рейтинг
        rating_text = self.rating_edit.text().strip().replace(",", ".")
        rating = None
        try:
            rating = float(rating_text)
            if not (0.0 <= rating <= 5.0):
                errors.append("Рейтинг должен быть от 0.0 до 5.0")
                rating = None
        except ValueError:
            errors.append("Рейтинг должен быть числом (например: 4.5)")

        # Дата
        public_date = self.public_date_calendar.selectedDate().toPyDate()

        # Жанры (необязательно — просто передаём выбранные)
        selected = self.genres_list_widget.selectedItems()
        genre_ids = [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in selected]
        genre_names = [item.text() for item in selected]

        # Файл книги
        book_path = self.book_path_edit.text().strip()
        if not book_path:
            errors.append("Необходимо выбрать файл книги")
        elif not os.path.exists(book_path):
            errors.append("Файл книги не найден по указанному пути")

        # Обложка (необязательна)
        cover_path = self.cover_path_edit.text().strip() or None
        if cover_path and not os.path.exists(cover_path):
            errors.append("Файл обложки не найден по указанному пути")

        # Отдельный вывод всех ошибок
        if errors:
            QtWidgets.QMessageBox.warning(
                self, "Ошибки заполнения",
                "\n".join(f"• {e}" for e in errors)
            )
            return None

        # Автоисправление поля в интерфейсе
        self.book_name_edit.setText(name)
        self.author_edit.setText(author)
        if summary:
            self.summary_text_edit.setPlainText(summary)

        return {
            "name": name,
            "author": author,
            "summary": summary,
            "rating": rating,
            "public_date": public_date.strftime("%d.%m.%Y"),
            "genre_ids": genre_ids,
            "genre_names": genre_names,
            "book_path": book_path,
            "cover_path": cover_path,
        }

    def _show_preview(self, data: dict) -> bool:
        """Показывает диалог с предпросмотром карточки, возвращает True при подтверждении"""
        from classes.classes import BookCard

        pixmap = QPixmap()
        if data["cover_path"]:
            pixmap.load(data["cover_path"])

        card = BookCard(
            name=data["name"],
            author=data["author"],
            public_date=datetime.strptime(data["public_date"], "%d.%m.%Y").date(),
            rating=data["rating"],
            genres=data["genre_names"],
            summary=data["summary"],
            pixmap=pixmap,
            file_path="",
        )

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Предпросмотр карточки")
        dialog.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowTitleHint)

        dialog.setFixedWidth(600)
        dialog.setFixedHeight(400)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.addWidget(card)

        note = QtWidgets.QLabel("Так будет выглядеть карточка книги. Добавить?")
        note.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)

        btn_layout = QtWidgets.QHBoxLayout()
        confirm_btn = QtWidgets.QPushButton("✓ Добавить")
        back_btn = QtWidgets.QPushButton("← Назад")
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(back_btn)
        layout.addLayout(btn_layout)

        confirm_btn.clicked.connect(dialog.accept)
        back_btn.clicked.connect(dialog.reject)

        return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

    def _on_add_book(self):
        """Вызываем добавление книги"""
        data = self._get_validated_data()
        if data is None:
            return

        print("check")
        # Показываем превью, если отменяет - не добавлять
        if not self._show_preview(data):
            return

        # Кодируем файл книги
        with open(data["book_path"], "rb") as f:
            book_b64 = base64.b64encode(f.read()).decode()

        # Кодируем обложку (если есть)
        cover_b64 = None
        cover_filename = None
        if data["cover_path"]:
            with open(data["cover_path"], "rb") as f:
                cover_b64 = base64.b64encode(f.read()).decode()
            cover_filename = os.path.basename(data["cover_path"])

        payload = json.dumps({
            "name": data["name"],
            "author": data["author"],
            "summary": data["summary"],
            "rating": data["rating"],
            "public_date": data["public_date"],
            "genre_ids": data["genre_ids"],
            "book_data": book_b64,
            "book_filename": os.path.basename(data["book_path"]),
            "cover_data": cover_b64,
            "cover_filename": cover_filename,
        }, ensure_ascii=False)

        self.book_add_requested.emit(payload)
        self.hide()

    # --- Файловые диалоги --------------------------------------
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
