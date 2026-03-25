from PyQt5 import QtCore, QtWidgets


class StatCard(QtWidgets.QFrame):
    def __init__(self, title: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        self.setMinimumHeight(116)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet(f"color: {accent}; font-weight: 700;")
        layout.addWidget(self.title_label)

        self.value_label = QtWidgets.QLabel("0")
        value_font = self.value_label.font()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        layout.addWidget(self.value_label)

        self.note_label = QtWidgets.QLabel("")
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("color: #62809b;")
        layout.addWidget(self.note_label)

        layout.addStretch(1)

    def set_value(self, value: str, note: str = "") -> None:
        self.value_label.setText(str(value))
        self.note_label.setText(note)


class SearchPanel(QtWidgets.QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("font-weight: 700; color: #17324d;")
        layout.addWidget(self.title_label)

        self.content_layout = QtWidgets.QGridLayout()
        self.content_layout.setHorizontalSpacing(10)
        self.content_layout.setVerticalSpacing(10)
        layout.addLayout(self.content_layout)

    def add_row(self, row: int, label: str, widget: QtWidgets.QWidget) -> None:
        caption = QtWidgets.QLabel(label)
        caption.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        self.content_layout.addWidget(caption, row, 0)
        self.content_layout.addWidget(widget, row, 1)

