from PyQt6 import QtWidgets
import windows.loginWindow as loginWindow
from client.socket_worker import SocketWorker


class Login(QtWidgets.QMainWindow, loginWindow.Ui_MainWindow):
    def __init__(self, socket_worker: SocketWorker):
        super().__init__()
        self.setupUi(self)
        self.socket_worker = socket_worker
        self._pending_action = None  # действие, отложенное до установки соединения

        with open("styles/loginStyle.qss", "r", encoding="utf-8") as file:
            self.setStyleSheet(file.read())

        # Заполняем поля значениями по умолчанию из socket_worker
        self.host_edit.setText(socket_worker.host)
        self.port_edit.setText(str(socket_worker.port))

        self.login_btn.clicked.connect(self.try_login)
        self.register_btn.clicked.connect(self.try_register)

        self.socket_worker.connected.connect(self._on_connected)
        self.socket_worker.error_occurred.connect(self._on_error)

    # --- Вспомогательные методы -------------------------------------------------------
    def _get_connection_params(self) -> tuple[str, int] | None:
        """Читает IP и порт из полей"""
        host = self.host_edit.text().strip() or self.host_edit.placeholderText()
        port_text = self.port_edit.text().strip() or self.port_edit.placeholderText()
        try:
            port = int(port_text)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Порт должен быть числом от 1 до 65535.")
            return None
        return host, port

    def _send_or_queue(self, payload: dict):
        """Если соединение уже есть — отправляем сразу.
        Иначе — сохраняем даннные и стартуем поток"""
        if self.socket_worker.is_connected:
            self.socket_worker.send_json(payload)
            return

        # Запускаем поток только если он ещё не запущен
        if not self.socket_worker.isRunning():
            params = self._get_connection_params()
            if params is None:
                return
            host, port = params
            self.socket_worker.set_connection_params(host, port)
            self.socket_worker.start()

        # В любом случае сохраняем действие — оно выполнится в _on_connected
        self._pending_action = payload

    def _on_connected(self):
        """Вызывается когда сокет успешно подключился."""
        if self._pending_action is not None:
            self.socket_worker.send_json(self._pending_action)
            self._pending_action = None

    def _on_error(self, message: str):
        self._pending_action = None  # сбрасываем отложенное действие при ошибке
        QtWidgets.QMessageBox.critical(self, "Ошибка", message)

    # --- Команды от кнопок ---------------------------------
    def try_login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        self._send_or_queue({"action": "login", "username": username, "password": password})

    def try_register(self):
        username = self.username_edit.text()
        password = self.password_edit.text()
        self._send_or_queue({"action": "register", "username": username, "password": password})