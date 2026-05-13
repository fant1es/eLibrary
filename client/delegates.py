from PyQt6.QtWidgets import QStyledItemDelegate, QDoubleSpinBox, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


def _setup_spin(parent, min_val, max_val, step, decimals):
    """Вспомогательный метод для создания спин боксов"""
    spin = QDoubleSpinBox(parent)
    spin.setRange(min_val, max_val)
    spin.setSingleStep(step)
    spin.setDecimals(decimals)
    spin.setFrame(True)
    spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    return spin


class RangeDelegate(QStyledItemDelegate):
    """Делегат для установки спинбоксов рейтинга и даты издания"""
    # Роли для доступа к конкретным данным
    RoleTag = Qt.ItemDataRole.UserRole + 1
    RoleMin = Qt.ItemDataRole.UserRole + 2
    RoleMax = Qt.ItemDataRole.UserRole + 3
    RoleStep = Qt.ItemDataRole.UserRole + 4
    RoleDecimals = Qt.ItemDataRole.UserRole + 5
    RoleName = Qt.ItemDataRole.UserRole + 6

    def createEditor(self, parent, option, index):
        if index.data(self.RoleTag) != "range_editor":
            return super().createEditor(parent, option, index)

        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)

        # Параметры из модели
        min_val = index.data(self.RoleMin) or 0
        max_val = index.data(self.RoleMax) or 100
        step = index.data(self.RoleStep) or 1
        decimals = index.data(self.RoleDecimals) or 0

        container.spin_from = _setup_spin(container, min_val, max_val, step, decimals)
        container.spin_to = _setup_spin(container, min_val, max_val, step, decimals)

        # Не даём выставить from > to
        container.spin_from.valueChanged.connect(container.spin_to.setMinimum)
        container.spin_to.valueChanged.connect(container.spin_from.setMaximum)

        # Обновляем модель сразу при подтверждении каждого спинбокса
        # иначе setModelData зовётся только при потере фокуса у всего делегата целиком
        container.spin_from.valueChanged.connect(lambda _: self.commitData.emit(container))
        container.spin_to.valueChanged.connect(lambda _: self.commitData.emit(container))

        name = index.data(self.RoleName) or ""
        layout.addWidget(QLabel(f"{name}: с", container))
        layout.addWidget(container.spin_from)
        layout.addWidget(QLabel("по", container))
        layout.addWidget(container.spin_to)

        container.setFocusProxy(container.spin_from)
        return container

    def setEditorData(self, editor, index):
        # Берем данные из EditRole или DisplayRole (для первого раза)
        text = index.data(Qt.ItemDataRole.EditRole) or index.data(Qt.ItemDataRole.DisplayRole)

        if not text:
            return

        try:
            # Парсим строку "Рейтинг: 1-5 ★"
            clean_text = text.split(":")[-1].strip().replace("★", "").strip()
            start, end = clean_text.split("-")
            editor.spin_from.setValue(float(start))
            editor.spin_to.setValue(float(end))
        except (ValueError, AttributeError, IndexError):
            # Если что-то пошло не так, спинбоксы останутся в значениях по умолчанию
            pass

    def setModelData(self, editor, model, index):
        name = index.data(self.RoleName)
        val_from = editor.spin_from.value()
        val_to = editor.spin_to.value()

        fmt = lambda v: str(int(v)) if v == int(v) else str(round(v, 1))

        star = " ★" if name == "Рейтинг" else ""
        result = f"{name}: {fmt(val_from)}-{fmt(val_to)}{star}"

        # Обновляем DisplayRole, чтобы текст в дереве изменился и сработал itemChanged
        model.blockSignals(True)
        model.setData(index, result, Qt.ItemDataRole.DisplayRole)
        model.setData(index, result, Qt.ItemDataRole.EditRole)
        model.blockSignals(False)

        model.itemChanged.emit(model.itemFromIndex(index))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)