APP_STYLESHEET = """
QWidget {
    background-color: #f4f7fb;
    color: #17324d;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QMainWindow, QDialog {
    background-color: #f4f7fb;
}

QFrame#cardFrame {
    background: #ffffff;
    border: 1px solid #d7e0ea;
    border-radius: 16px;
}

QLabel#titleLabel {
    font-size: 20pt;
    font-weight: 700;
    color: #0f2740;
}

QLabel#subtitleLabel {
    color: #58738f;
}

QLabel#roleBadge {
    background: #dff0ff;
    color: #1b5a91;
    border-radius: 10px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton {
    background: #1f6fb2;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background: #185c93;
}

QPushButton:disabled {
    background: #b9c8d8;
    color: #eef3f7;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit, QTextEdit {
    background: white;
    border: 1px solid #c8d4df;
    border-radius: 10px;
    padding: 7px 10px;
}

QTabWidget::pane {
    border: 1px solid #d7e0ea;
    background: #ffffff;
    border-radius: 14px;
}

QTabBar::tab {
    background: #dde8f2;
    color: #274866;
    padding: 10px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #0f2740;
    font-weight: 700;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f7fafc;
    border: 1px solid #d7e0ea;
    border-radius: 12px;
    gridline-color: #e2e9f0;
}

QHeaderView::section {
    background: #eaf1f7;
    color: #183550;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #d7e0ea;
    font-weight: 600;
}

QGroupBox {
    border: 1px solid #d7e0ea;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
"""

