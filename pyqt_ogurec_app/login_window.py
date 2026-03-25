from PyQt5 import QtCore, QtWidgets

from pyqt_ogurec_app.auth import User, authenticate
from pyqt_ogurec_app.config import APP_SUBTITLE, APP_TITLE


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user: User | None = None

        self.setWindowTitle(f"{APP_TITLE} - Авторизация")
        self.resize(430, 290)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title_label = QtWidgets.QLabel(APP_TITLE)
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(APP_SUBTITLE)
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        form_card = QtWidgets.QFrame()
        form_card.setObjectName("cardFrame")
        form_layout = QtWidgets.QFormLayout(form_card)
        form_layout.setContentsMargins(18, 18, 18, 18)
        form_layout.setSpacing(12)

        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("admin / manager / viewer")
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        layout.addWidget(form_card)

        info_label = QtWidgets.QLabel(
            "Демо-доступ: admin/admin, manager/manager, viewer/viewer"
        )
        info_label.setWordWrap(True)
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        info_label.setStyleSheet("color: #5b7690;")
        layout.addWidget(info_label)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setAlignment(QtCore.Qt.AlignCenter)
        self.error_label.setStyleSheet("color: #b42318; font-weight: 600;")
        layout.addWidget(self.error_label)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        user = authenticate(username, password)
        if not user:
            self.error_label.setText("Неверный логин или пароль.")
            return
        self.user = user
        self.error_label.clear()
        super().accept()
