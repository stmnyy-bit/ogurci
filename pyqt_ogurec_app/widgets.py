from PyQt5 import QtCore, QtWidgets


class SearchPanel(QtWidgets.QGroupBox):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.content_layout = QtWidgets.QGridLayout(self)
        self.content_layout.setContentsMargins(10, 16, 10, 10)
        self.content_layout.setHorizontalSpacing(8)
        self.content_layout.setVerticalSpacing(8)

    def add_row(self, row: int, label: str, widget: QtWidgets.QWidget) -> None:
        caption = QtWidgets.QLabel(label)
        caption.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.content_layout.addWidget(caption, row, 0)
        self.content_layout.addWidget(widget, row, 1)


class SummaryPanel(QtWidgets.QGroupBox):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 10)
        self.summary_label = QtWidgets.QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

    def set_text(self, text: str) -> None:
        self.summary_label.setText(text)

