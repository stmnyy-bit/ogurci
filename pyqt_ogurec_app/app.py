import sys
import types
from pathlib import Path


def _bootstrap_package() -> None:
    if __package__ not in (None, "") and "pyqt_ogurec_app" in sys.modules:
        return

    package_root = Path(__file__).resolve().parent
    project_root = package_root.parent

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    package = sys.modules.get("pyqt_ogurec_app")
    if package is None:
        package = types.ModuleType("pyqt_ogurec_app")
        package.__file__ = str(package_root / "__init__.py")
        package.__path__ = [str(package_root)]
        sys.modules["pyqt_ogurec_app"] = package


_bootstrap_package()

from PyQt5 import QtWidgets

from pyqt_ogurec_app.config import APP_TITLE, resolve_default_db_path
from pyqt_ogurec_app.login_window import LoginDialog
from pyqt_ogurec_app.main_window import MainWindow
from pyqt_ogurec_app.styles import APP_STYLESHEET


def create_application(argv: list[str]) -> QtWidgets.QApplication:
    app = QtWidgets.QApplication(argv)
    app.setApplicationName(APP_TITLE)
    app.setQuitOnLastWindowClosed(True)
    app.setStyleSheet(APP_STYLESHEET)
    return app


def main() -> int:
    app = create_application(sys.argv)

    login_dialog = LoginDialog()
    if login_dialog.exec_() != QtWidgets.QDialog.Accepted or not login_dialog.user:
        return 0

    window = MainWindow(login_dialog.user, resolve_default_db_path())
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
