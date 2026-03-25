from PyQt5 import QtWidgets

from pyqt_ogurec_app.auth import User, authenticate


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user: User | None = None

        self.setWindowTitle("Авторизация")
        self.setFixedSize(320, 180)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(8)

        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("admin / manager / viewer")
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        layout.addLayout(form_layout)

        info_label = QtWidgets.QLabel("admin/admin, manager/manager, viewer/viewer")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #aa0000;")
        layout.addWidget(self.error_label)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

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
