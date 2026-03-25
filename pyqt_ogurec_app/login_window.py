from PyQt5 import QtCore, QtWidgets

from pyqt_ogurec_app.auth import User, authenticate
from pyqt_ogurec_app.config import APP_SUBTITLE, APP_TITLE


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user: User | None = None

        self.setWindowTitle(APP_TITLE)
        self.resize(360, 220)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title_label = QtWidgets.QLabel("Авторизация")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(APP_SUBTITLE)
        layout.addWidget(subtitle_label)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(8)

        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("admin / manager / viewer")
        self.username_edit.setClearButtonEnabled(True)
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setClearButtonEnabled(True)

        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        layout.addLayout(form_layout)

        info_label = QtWidgets.QLabel(
            "Демо-доступ: admin/admin, manager/manager, viewer/viewer"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #aa0000;")
        layout.addWidget(self.error_label)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.accept)
        self.username_edit.setFocus()

    def accept(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        user = authenticate(username, password)
        if not user:
            self.error_label.setText("Неверный логин или пароль")
            return
        self.user = user
        self.error_label.clear()
        super().accept()
