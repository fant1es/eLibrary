from datetime import datetime
import base64
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout, QMessageBox
from PyQt6.QtCore import QByteArray, Qt

# from rapidfuzz import process, fuzz

from classes.classes import BookCard
from client.delegates import RangeDelegate
from windows import clientWindow
from windows.window_classes import AddBookWin, SelectBookWin


class Client(QtWidgets.QMainWindow, clientWindow.Ui_MainWindow):
    def __init__(self, socket_worker, user_role):
        super().__init__()
        self.setupUi(self)

        with open("styles/style.qss", "r", encoding="utf-8") as file:
            self.setStyleSheet(file.read())

        self.all_books = []
        self.all_genres = []
        self.scroll_area.setWidgetResizable(True)
        self.user_role = user_role
        self.setup_permissions()

        # --- Окна администратора ------------------------------
        # --- Окно добавления/редактирования (универсальное) ------------
        self.add_book_btn.clicked.connect(self.add_book_print)
        self.add_book_window = AddBookWin()

        self.add_book_window.book_add_requested.connect(
            lambda payload: self.socket_worker.send(f"add_book|{payload}")
        )
        self.add_book_window.book_edit_requested.connect(
            lambda payload: self.socket_worker.send(f"edit_book|{payload}")
        )

        self.add_book_window.genre_add_requested.connect(
            lambda name: self.socket_worker.send(f"add_genre|{name}")
        )
        self.add_book_window.genre_delete_requested.connect(
            lambda ids: self.socket_worker.send(f"delete_genres|{','.join(map(str, ids))}")
        )

        # --- Окно удаления книги ------------------------------
        self.del_book_btn.clicked.connect(self.delete_book_print)
        self.delete_book_window = SelectBookWin(mode="delete", parent=self)
        self.delete_book_window.book_selected.connect(
            lambda book_id: self.socket_worker.send(f"delete_book|{book_id}")
        )

        # --- Окно изменения книги ------------------------------
        self.edit_book_btn.clicked.connect(self.edit_book_print)
        self.edit_book_window = SelectBookWin(mode="edit", parent=self)
        # Вызываем переход к универсальному окну
        self.edit_book_window.book_selected.connect(self.on_book_selected_for_edit)

        # --- Установка потока с сокетом -----------------------
        self.socket_worker = socket_worker

        # Запрашиваем необходимые данные
        self.socket_worker.send("get_books")
        self.socket_worker.send("get_genres")

        self.socket_worker.error_occurred.connect(self.show_error)
        self.socket_worker.books_received.connect(self.on_books_received)
        self.socket_worker.genres_received.connect(self.on_genres_received)
        self.socket_worker.file_received.connect(self.save_file)

        self.socket_worker.start()

        # --- Установка дерева с фильтрами ---------------------
        self.tree_model = self._setup_filter_tree()
        self.filter_tree.setModel(self.tree_model)
        self.filter_tree.expandAll()

        self.filter_tree.setIndentation(20)
        self.filter_tree.setAnimated(True)
        self.filter_tree.setAlternatingRowColors(True)
        self.filter_tree.setUniformRowHeights(False)

        self.range_delegate = RangeDelegate()
        self.filter_tree.setItemDelegate(self.range_delegate)

        # Подключаем сигнал изменения модели к фильтрации
        self.tree_model.itemChanged.connect(self.apply_filters)

        # --- Привязка событий под кнопки и триггеры ------------
        self.exit_btn.clicked.connect(self.exit)
        self.exit_action.triggered.connect(self.exit)

    def setup_permissions(self):
        """Скрывает или показывает кнопки управления в зависимости от роли"""
        is_admin = (self.user_role == "admin")

        # Если не админ — скрываем кнопки
        self.add_book_btn.setVisible(is_admin)
        self.del_book_btn.setVisible(is_admin)
        self.edit_book_btn.setVisible(is_admin)

        if not is_admin:
            print("Доступ ограничен: режим пользователя")

    def add_book_print(self):
        if self.add_book_window.isHidden():
            try:
                with open("styles/addBookStyle.qss", "r", encoding="utf-8") as file:
                    self.add_book_window.setStyleSheet(file.read())
            except FileNotFoundError:
                print("Файл стилей не найден.")

            # Сброс режима на "добавление"
            self.add_book_window.reset()
            # Передаем актуальные жанры перед показом
            self.add_book_window.set_genres(self.all_genres)
            self.add_book_window.show()

    def delete_book_print(self):
        if not self.all_books:
            QMessageBox.information(self, "Инфо", "Список книг пуст")
            return

        # Передаем все книги для карточек
        self.delete_book_window.refresh_books(self.all_books)
        self.delete_book_window.exec()

    def edit_book_print(self):
        if not self.all_books:
            QMessageBox.information(self, "Инфо", "Список книг пуст")
            return
        self.edit_book_window.refresh_books(self.all_books)
        self.edit_book_window.exec()

    def on_book_selected_for_edit(self, book_id: int):
        # Находим книгу по ID
        book_data = next((b for b in self.all_books if b["id"] == book_id), None)
        if book_data:
            try:
                with open("styles/addBookStyle.qss", "r", encoding="utf-8") as file:
                    self.add_book_window.setStyleSheet(file.read())
            except FileNotFoundError:
                print("Файл стилей не найден.")

            self.add_book_window.load_for_edit(book_data, self.all_genres)
            self.add_book_window.show()

    # --- Работа с жанрами --------------------------------------
    def on_genres_received(self, genres: list[dict]):
        self.all_genres = genres.copy()
        # Обновляем виджет, если окно открыто
        if not self.add_book_window.isHidden():
            self.add_book_window.set_genres(self.all_genres)
        # Обновляем фильтр жанров в дереве
        self._update_genre_filters(self.all_genres)

    # --- Работа с книгами --------------------------------------
    def on_books_received(self, books: list[dict]):
        # Предварительная обработка обложек для быстрой отрисовки книг
        for book in books:
            if book.get("cover_pic"):
                pix = QPixmap()
                pix.loadFromData(QByteArray(base64.b64decode(book["cover_pic"])))
                book["cached_pixmap"] = pix
            else:
                # Заглушка
                book["cached_pixmap"] = QPixmap()

        self.all_books = books.copy()
        # Обновляем список авторов в фильтре
        self._update_author_filters(self.all_books)
        # Применяем текущие фильтры
        self.apply_filters()

    # --- Фильтрация ------------------------------------------------
    def _update_genre_filters(self, genres: list[dict]):
        """Перестраивает чекбоксы жанров в дереве фильтров."""
        self.tree_model.blockSignals(True)
        self.genre_filter_item.removeRows(0, self.genre_filter_item.rowCount())

        for genre in genres:
            # Жанр может быть словарем или просто строкой
            name = genre.get("name", str(genre)) if isinstance(genre, dict) else str(genre)
            child = QStandardItem(name)
            child.setCheckable(True)
            child.setCheckState(Qt.CheckState.Unchecked)
            self.genre_filter_item.appendRow(child)

        self.filter_tree.expand(self.genre_filter_item.index())
        self.tree_model.blockSignals(False)

    def _update_author_filters(self, books: list[dict]):
        """Перестраивает чекбоксы авторов в дереве фильтров, сохраняя отмеченные."""
        # Запоминаем уже отмеченных авторов, чтобы не сбрасывать выбор при обновлении
        checked_before = set()
        for row in range(self.author_filter_item.rowCount()):
            child = self.author_filter_item.child(row)
            if child.checkState() == Qt.CheckState.Checked:
                checked_before.add(child.text())

        self.tree_model.blockSignals(True)
        self.author_filter_item.removeRows(0, self.author_filter_item.rowCount())

        unique_authors = sorted({b["author"] for b in books if b.get("author")})
        for author in unique_authors:
            child = QStandardItem(author)
            child.setCheckable(True)
            child.setCheckState(
                Qt.CheckState.Checked if author in checked_before else Qt.CheckState.Unchecked
            )
            self.author_filter_item.appendRow(child)

        self.filter_tree.expand(self.author_filter_item.index())
        self.tree_model.blockSignals(False)

    def _read_filter_state(self) -> dict:
        """Читает текущее состояние всего дерева фильтров"""
        state = {
            "genres": set(),
            "authors": set(),
            "date_from": 1800,
            "date_to": 2026,
            "rating_from": 1.0,
            "rating_to": 5.0,
        }

        for row in range(self.tree_model.rowCount()):
            item = self.tree_model.item(row)

            # Авторы / Жанры
            if item.hasChildren():
                for child_row in range(item.rowCount()):
                    child = item.child(child_row)
                    if child.checkState() == Qt.CheckState.Checked:
                        if item is self.genre_filter_item:
                            state["genres"].add(child.text())
                        elif item is self.author_filter_item:
                            state["authors"].add(child.text())
                continue

            # Диапазоны (Делегаты)
            if item.data(RangeDelegate.RoleTag) != "range_editor":
                continue

            name = item.data(RangeDelegate.RoleName)
            # Текущее значение хранится в EditRole как строка вида "Рейтинг: 1-5 ★"
            raw = item.data(Qt.ItemDataRole.DisplayRole)
            try:
                # Берём часть после ":" и убираем звёздочку
                clean = raw.split(":")[-1].strip().replace("★", "").strip()
                lo_str, hi_str = clean.split("-")
                lo, hi = float(lo_str), float(hi_str)
            except (ValueError, AttributeError):
                continue

            if name == "Дата издания":
                state["date_from"] = int(lo)
                state["date_to"] = int(hi)
            elif name == "Рейтинг":
                state["rating_from"] = lo
                state["rating_to"] = hi

        return state

    def apply_filters(self):
        """Фильтрует all_books по текущему состоянию дерева и перерисовывает карточки."""
        if not self.all_books:
            return

        f = self._read_filter_state()

        filtered = []
        for book in self.all_books:
            # Жанры
            if f["genres"]:
                # book["genres"] может быть list[str] или list[dict]
                book_genre_names = {
                    g.get("name", str(g)) if isinstance(g, dict) else str(g)
                    for g in book.get("genres", [])
                }
                if not book_genre_names.intersection(f["genres"]):
                    continue

            # Авторы
            if f["authors"] and book.get("author") not in f["authors"]:
                continue

            # Дата издания
            try:
                year = datetime.strptime(book["public_date"], "%d.%m.%Y").year
                if not (f["date_from"] <= year <= f["date_to"]):
                    continue
            except (ValueError, KeyError):
                pass

            # Рейтинг
            try:
                rating = float(book.get("rating", 0))
                if not (f["rating_from"] <= rating <= f["rating_to"]):
                    continue
                print(book["rating"])

            except (ValueError, TypeError):
                print(f"Ошибка рейтинга для книги {book.get('name')}")
                continue  # Если данные битые, лучше скрыть книгу, чем сломать фильтр

            filtered.append(book)

        self._render_books(filtered)

    def _render_books(self, books: list[dict]):
        """Отрисовывает карточки переданного списка книг"""
        layout = self.scrollAreaWidgetContents.layout() or QVBoxLayout(self.scrollAreaWidgetContents)

        # Удаляем старые карточки
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for book in books:
            cover_b64 = book.get("cover_pic")
            if cover_b64:
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(base64.b64decode(cover_b64)))
            else:
                pixmap = QPixmap()

            book_card = BookCard(
                name=book["name"],
                author=book["author"],
                public_date=datetime.strptime(book["public_date"], "%d.%m.%Y").date(),
                rating=book["rating"],
                genres=book["genres"],
                summary=book["summary"],
                file_path=book["file_path"],
                pixmap=book.get("cached_pixmap", QPixmap())
            )
            book_card.download_requested.connect(self.socket_worker.request_download)
            layout.addWidget(book_card)

        layout.addStretch()
        self.scrollAreaWidgetContents.adjustSize()
        self.scroll_area.update()

    # --- Прочее ----------------------------------------
    def save_file(self, filename: str, data: bytes):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить книгу", filename)
        if path:
            with open(path, "wb") as f:
                f.write(data)

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Ошибка")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def exit(self):
        self.socket_worker.stop()
        self.socket_worker.wait()
        self.close()

    # --- Построение дерева фильтров ----------------------------
    def _setup_filter_tree(self) -> QStandardItemModel:
        """Строит модель дерева фильтров и сохраняет ссылки на узлы Авторов и Жанров."""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Фильтры"])

        # Авторы
        self.author_filter_item = QStandardItem("Авторы:")
        self.author_filter_item.setEditable(False)
        model.appendRow(self.author_filter_item)

        # Жанры
        self.genre_filter_item = QStandardItem("Жанры:")
        self.genre_filter_item.setEditable(False)
        model.appendRow(self.genre_filter_item)

        # Диапазоны
        model.appendRow(_create_range_item("Дата издания", "1800-2026", 1800, 2026, 1, 0))
        model.appendRow(_create_range_item("Рейтинг", "1-5 ★", 1, 5, 0.5, 1))

        return model


# --- Вспомогательные функции модуля ------------------------------------
def _create_range_item(name: str, start_val, min_val, max_val, step, decimal) -> QStandardItem:
    item = QStandardItem(f"{name}: {start_val}")
    item.setEditable(True)
    item.setData("range_editor", RangeDelegate.RoleTag)
    item.setData(min_val, RangeDelegate.RoleMin)
    item.setData(max_val, RangeDelegate.RoleMax)
    item.setData(step, RangeDelegate.RoleStep)
    item.setData(decimal, RangeDelegate.RoleDecimals)
    item.setData(name, RangeDelegate.RoleName)
    return item
