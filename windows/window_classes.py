from windows import addBookWidget
from PyQt6 import QtWidgets, QtCore, QtGui


class AddBookWin(QtWidgets.QWidget, addBookWidget.Ui_addBookWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowTitleHint)
