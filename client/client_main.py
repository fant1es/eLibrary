from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
from windows import clientWindow
# Импортируем наш новый делегат
from client.delegates import RangeDelegate


class Client(QtWidgets.QMainWindow, clientWindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.tree_model = setup_filter_tree()
        self.filter_tree.setModel(self.tree_model)
        self.filter_tree.expandAll()

        self.filter_tree.setIndentation(20)
        self.filter_tree.setAnimated(True)
        self.filter_tree.setAlternatingRowColors(True)
        self.filter_tree.setUniformRowHeights(False)

        # Назначаем наш умный делегат на дерево
        self.range_delegate = RangeDelegate(self.filter_tree)
        self.filter_tree.setItemDelegate(self.range_delegate)

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
    model.appendRow(create_range_item("Рейтинг", "1-5", 1, 5, 0.5, 1))

    return model
