import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt5 import QtWidgets
from pyqt_ogurec_app.config import APP_TITLE, resolve_default_db_path
from pyqt_ogurec_app.login_window import LoginDialog
from pyqt_ogurec_app.main_window import MainWindow
from pyqt_ogurec_app.styles import APP_STYLESHEET

def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyleSheet(APP_STYLESHEET)

    login_dialog = LoginDialog()
    if login_dialog.exec_() != QtWidgets.QDialog.Accepted or not login_dialog.user:
        return 0

    window = MainWindow(login_dialog.user, resolve_default_db_path())
    window.show()
    return app.exec_()

if __name__ == "__main__":
    raise SystemExit(main())
