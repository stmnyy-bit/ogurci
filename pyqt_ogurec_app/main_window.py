import csv
from pathlib import Path

from PyQt5 import QtCore, QtWidgets

from pyqt_ogurec_app.config import APP_TITLE
from pyqt_ogurec_app.database import ALL_MANUFACTURERS, ALL_PLACES, DatabaseManager
from pyqt_ogurec_app.dialogs import ClientDialog, TelevisionDialog
from pyqt_ogurec_app.widgets import DataTable


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, user, db_path: str):
        super().__init__()
        self.user = user
        self.db = DatabaseManager(db_path)
        self.television_rows = []
        self.customer_rows = []
        self.order_rows = []
        self.all_view_rows = []
        self.current_view_rows = []
        self.current_view_columns = []

        self.setWindowTitle(f"{APP_TITLE} - {user.display_name}")
        self.resize(1200, 820)

        self._build_ui()
        self._connect_signals()
        self._apply_permissions()
        self.connect_database(initial=True)

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root_layout = QtWidgets.QGridLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setHorizontalSpacing(10)
        root_layout.setVerticalSpacing(10)

        root_layout.addWidget(self._build_database_group(), 0, 0, 1, 2)
        root_layout.addWidget(self._build_televisions_group(), 1, 0)
        root_layout.addWidget(self._build_customers_group(), 1, 1)
        root_layout.addWidget(self._build_orders_group(), 2, 0)
        root_layout.addWidget(self._build_views_group(), 2, 1)

        root_layout.setColumnStretch(0, 1)
        root_layout.setColumnStretch(1, 1)
        root_layout.setRowStretch(1, 3)
        root_layout.setRowStretch(2, 3)

        self.stats_label = QtWidgets.QLabel("")
        self.statusBar().addPermanentWidget(self.stats_label)
        self.statusBar().showMessage("Готово к работе")

    def _build_database_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Подключение к базе")
        layout = QtWidgets.QGridLayout(group)

        layout.addWidget(QtWidgets.QLabel("Файл базы:"), 0, 0)
        self.db_path_edit = QtWidgets.QLineEdit(self.db.db_path)
        layout.addWidget(self.db_path_edit, 0, 1)

        self.browse_db_button = QtWidgets.QPushButton("Выбрать")
        self.reconnect_button = QtWidgets.QPushButton("Открыть")
        layout.addWidget(self.browse_db_button, 0, 2)
        layout.addWidget(self.reconnect_button, 0, 3)

        layout.addWidget(QtWidgets.QLabel("Структура базы: televisions, customers, orders"), 1, 0, 1, 4)
        return group

    def _build_televisions_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Таблица televisions")
        layout = QtWidgets.QVBoxLayout(group)

        filter_layout = QtWidgets.QGridLayout()
        self.tv_search_edit = QtWidgets.QLineEdit()
        self.tv_search_edit.setPlaceholderText("Код, модель или производитель")
        self.tv_manufacturer_combo = QtWidgets.QComboBox()
        self.tv_discount_spin = QtWidgets.QSpinBox()
        self.tv_discount_spin.setRange(0, 100)
        self.tv_sort_combo = QtWidgets.QComboBox()
        self.tv_sort_combo.addItem("Цена по убыванию", "price_desc")
        self.tv_sort_combo.addItem("Цена по возрастанию", "price_asc")
        self.tv_sort_combo.addItem("Скидка по убыванию", "discount_desc")
        self.tv_sort_combo.addItem("Модель А-Я", "model_asc")

        filter_layout.addWidget(QtWidgets.QLabel("Поиск:"), 0, 0)
        filter_layout.addWidget(self.tv_search_edit, 0, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Производитель:"), 1, 0)
        filter_layout.addWidget(self.tv_manufacturer_combo, 1, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Мин. скидка:"), 2, 0)
        filter_layout.addWidget(self.tv_discount_spin, 2, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Сортировка:"), 3, 0)
        filter_layout.addWidget(self.tv_sort_combo, 3, 1)
        layout.addLayout(filter_layout)

        button_row = QtWidgets.QHBoxLayout()
        self.add_tv_button = QtWidgets.QPushButton("Добавить")
        self.edit_tv_button = QtWidgets.QPushButton("Изменить")
        self.delete_tv_button = QtWidgets.QPushButton("Удалить")
        self.refresh_tv_button = QtWidgets.QPushButton("Обновить")
        for button in (
            self.add_tv_button,
            self.edit_tv_button,
            self.delete_tv_button,
            self.refresh_tv_button,
        ):
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.television_table = self._create_table_widget()
        layout.addWidget(self.television_table, stretch=1)
        return group

    def _build_customers_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Таблица customers")
        layout = QtWidgets.QVBoxLayout(group)

        filter_layout = QtWidgets.QGridLayout()
        self.customer_search_edit = QtWidgets.QLineEdit()
        self.customer_search_edit.setPlaceholderText("ID, ФИО или город")
        self.customer_place_combo = QtWidgets.QComboBox()
        self.customer_sort_combo = QtWidgets.QComboBox()
        self.customer_sort_combo.addItem("ФИО А-Я", "name_asc")
        self.customer_sort_combo.addItem("Город А-Я", "place_asc")
        self.customer_sort_combo.addItem("ID по возрастанию", "id_asc")
        self.customer_sort_combo.addItem("ID по убыванию", "id_desc")

        filter_layout.addWidget(QtWidgets.QLabel("Поиск:"), 0, 0)
        filter_layout.addWidget(self.customer_search_edit, 0, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Город:"), 1, 0)
        filter_layout.addWidget(self.customer_place_combo, 1, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Сортировка:"), 2, 0)
        filter_layout.addWidget(self.customer_sort_combo, 2, 1)
        layout.addLayout(filter_layout)

        button_row = QtWidgets.QHBoxLayout()
        self.refresh_customer_button = QtWidgets.QPushButton("Обновить")
        button_row.addWidget(self.refresh_customer_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.customer_table = self._create_table_widget()
        layout.addWidget(self.customer_table, stretch=1)
        return group

    def _build_orders_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Таблица orders")
        layout = QtWidgets.QVBoxLayout(group)

        filter_layout = QtWidgets.QGridLayout()
        self.order_search_edit = QtWidgets.QLineEdit()
        self.order_search_edit.setPlaceholderText("Номер заказа, customer_id, tv_code или дата")
        self.order_sort_combo = QtWidgets.QComboBox()
        self.order_sort_combo.addItem("Новые сверху", "date_desc")
        self.order_sort_combo.addItem("Старые сверху", "date_asc")
        self.order_sort_combo.addItem("Номер по возрастанию", "order_asc")
        self.order_sort_combo.addItem("Количество по убыванию", "quantity_desc")

        filter_layout.addWidget(QtWidgets.QLabel("Поиск:"), 0, 0)
        filter_layout.addWidget(self.order_search_edit, 0, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Сортировка:"), 1, 0)
        filter_layout.addWidget(self.order_sort_combo, 1, 1)
        layout.addLayout(filter_layout)

        button_row = QtWidgets.QHBoxLayout()
        self.add_order_button = QtWidgets.QPushButton("Добавить")
        self.edit_order_button = QtWidgets.QPushButton("Изменить")
        self.delete_order_button = QtWidgets.QPushButton("Удалить")
        self.refresh_order_button = QtWidgets.QPushButton("Обновить")
        for button in (
            self.add_order_button,
            self.edit_order_button,
            self.delete_order_button,
            self.refresh_order_button,
        ):
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.order_table = self._create_table_widget()
        layout.addWidget(self.order_table, stretch=1)
        return group

    def _build_views_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Представления")
        layout = QtWidgets.QVBoxLayout(group)

        filter_layout = QtWidgets.QGridLayout()
        self.view_combo = QtWidgets.QComboBox()
        self.view_search_edit = QtWidgets.QLineEdit()
        self.view_search_edit.setPlaceholderText("Поиск по строкам представления")
        filter_layout.addWidget(QtWidgets.QLabel("Представление:"), 0, 0)
        filter_layout.addWidget(self.view_combo, 0, 1)
        filter_layout.addWidget(QtWidgets.QLabel("Поиск:"), 1, 0)
        filter_layout.addWidget(self.view_search_edit, 1, 1)
        layout.addLayout(filter_layout)

        button_row = QtWidgets.QHBoxLayout()
        self.refresh_view_button = QtWidgets.QPushButton("Обновить")
        self.export_view_button = QtWidgets.QPushButton("Экспорт CSV")
        button_row.addWidget(self.refresh_view_button)
        button_row.addWidget(self.export_view_button)
        layout.addLayout(button_row)

        self.view_table = self._create_table_widget()
        layout.addWidget(self.view_table, stretch=1)

        layout.addWidget(QtWidgets.QLabel("SQL-код представления:"))
        self.view_sql_text = QtWidgets.QPlainTextEdit()
        self.view_sql_text.setReadOnly(True)
        self.view_sql_text.setMaximumHeight(160)
        layout.addWidget(self.view_sql_text)
        return group

    def _create_table_widget(self) -> QtWidgets.QTableWidget:
        return DataTable()

    def _connect_signals(self) -> None:
        self.browse_db_button.clicked.connect(self.choose_database_file)
        self.reconnect_button.clicked.connect(self.connect_database)

        self.tv_search_edit.textChanged.connect(self.load_televisions)
        self.tv_manufacturer_combo.currentTextChanged.connect(self.load_televisions)
        self.tv_discount_spin.valueChanged.connect(self.load_televisions)
        self.tv_sort_combo.currentIndexChanged.connect(self.load_televisions)
        self.refresh_tv_button.clicked.connect(self.load_televisions)
        self.add_tv_button.clicked.connect(self.add_television)
        self.edit_tv_button.clicked.connect(self.edit_television)
        self.delete_tv_button.clicked.connect(self.delete_television)
        self.television_table.itemDoubleClicked.connect(lambda *_: self.edit_television())

        self.customer_search_edit.textChanged.connect(self.load_customers)
        self.customer_place_combo.currentTextChanged.connect(self.load_customers)
        self.customer_sort_combo.currentIndexChanged.connect(self.load_customers)
        self.refresh_customer_button.clicked.connect(self.load_customers)

        self.order_search_edit.textChanged.connect(self.load_orders)
        self.order_sort_combo.currentIndexChanged.connect(self.load_orders)
        self.refresh_order_button.clicked.connect(self.load_orders)
        self.add_order_button.clicked.connect(self.add_order)
        self.edit_order_button.clicked.connect(self.edit_order)
        self.delete_order_button.clicked.connect(self.delete_order)
        self.order_table.itemDoubleClicked.connect(lambda *_: self.edit_order())

        self.view_combo.currentTextChanged.connect(self.load_current_view)
        self.view_search_edit.textChanged.connect(self.filter_view_rows)
        self.refresh_view_button.clicked.connect(self.load_current_view)
        self.export_view_button.clicked.connect(self.export_view_to_csv)

    def _apply_permissions(self) -> None:
        self.add_tv_button.setEnabled(self.user.can_add)
        self.edit_tv_button.setEnabled(self.user.can_edit)
        self.delete_tv_button.setEnabled(self.user.can_delete)
        self.add_order_button.setEnabled(self.user.can_add)
        self.edit_order_button.setEnabled(self.user.can_edit)
        self.delete_order_button.setEnabled(self.user.can_delete)

    def choose_database_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите файл базы данных",
            self.db_path_edit.text().strip() or str(Path.cwd()),
            "SQLite (*.db *.sqlite *.sqlite3);;Все файлы (*)",
        )
        if path:
            self.db_path_edit.setText(path)
            self.connect_database()

    def connect_database(self, initial: bool = False) -> None:
        path = self.db_path_edit.text().strip()
        if not path:
            if not initial:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Укажите путь к файлу базы данных.")
            return
        try:
            self.db.set_path(path)
            self.refresh_reference_data()
            self.refresh_dashboard()
            self.load_televisions()
            self.load_customers()
            self.load_orders()
            self.load_current_view()
            db_name = Path(path).name
            self.setWindowTitle(f"{APP_TITLE} - {self.user.display_name} - {db_name}")
            self.statusBar().showMessage(f"Подключено к базе: {path}")
        except Exception as exc:
            self.statusBar().showMessage(str(exc))
            if not initial:
                QtWidgets.QMessageBox.critical(self, "Ошибка подключения", str(exc))

    def refresh_reference_data(self) -> None:
        manufacturers = [ALL_MANUFACTURERS] + self.db.list_manufacturers()
        current_manufacturer = self.tv_manufacturer_combo.currentText()
        self.tv_manufacturer_combo.blockSignals(True)
        self.tv_manufacturer_combo.clear()
        self.tv_manufacturer_combo.addItems(manufacturers)
        index = self.tv_manufacturer_combo.findText(current_manufacturer)
        self.tv_manufacturer_combo.setCurrentIndex(max(index, 0))
        self.tv_manufacturer_combo.blockSignals(False)

        places = [ALL_PLACES] + self.db.list_places()
        current_place = self.customer_place_combo.currentText()
        self.customer_place_combo.blockSignals(True)
        self.customer_place_combo.clear()
        self.customer_place_combo.addItems(places)
        index = self.customer_place_combo.findText(current_place)
        self.customer_place_combo.setCurrentIndex(max(index, 0))
        self.customer_place_combo.blockSignals(False)

        current_view = self.view_combo.currentText()
        view_names = self.db.list_views()
        self.view_combo.blockSignals(True)
        self.view_combo.clear()
        self.view_combo.addItems(view_names)
        if current_view in view_names:
            self.view_combo.setCurrentText(current_view)
        self.view_combo.blockSignals(False)

    def refresh_dashboard(self) -> None:
        stats = self.db.dashboard_stats()
        self.stats_label.setText(
            f'Телевизоры: {stats["television_count"]} | '
            f'Клиенты: {stats["customer_count"]} | '
            f'Заказы: {stats["order_count"]} | '
            f'Представления: {stats["view_count"]}'
        )

    def load_televisions(self) -> None:
        if not self.db.connection:
            return
        self.television_rows = self.db.get_televisions(
            search=self.tv_search_edit.text().strip(),
            manufacturer=self.tv_manufacturer_combo.currentText(),
            min_discount=self.tv_discount_spin.value(),
            sort_mode=self.tv_sort_combo.currentData(),
        )
        self.fill_table(
            self.television_table,
            self.television_rows,
            ["tv_code", "model_name", "manufacturer", "diagonal_cm", "price", "discount_percent"],
        )

    def load_customers(self) -> None:
        if not self.db.connection:
            return
        self.customer_rows = self.db.get_customers(
            search=self.customer_search_edit.text().strip(),
            place=self.customer_place_combo.currentText(),
            sort_mode=self.customer_sort_combo.currentData(),
        )
        self.fill_table(
            self.customer_table,
            self.customer_rows,
            ["customer_id", "full_name", "place"],
        )

    def load_orders(self) -> None:
        if not self.db.connection:
            return
        self.order_rows = self.db.get_orders(
            search=self.order_search_edit.text().strip(),
            sort_mode=self.order_sort_combo.currentData(),
        )
        self.fill_table(
            self.order_table,
            self.order_rows,
            ["order_number", "customer_id", "tv_code", "order_date", "quantity", "discount_percent"],
        )

    def load_current_view(self) -> None:
        if not self.db.connection:
            return
        view_name = self.view_combo.currentText().strip()
        if not view_name:
            self.current_view_columns = []
            self.all_view_rows = []
            self.current_view_rows = []
            self.fill_table(self.view_table, [], [])
            self.view_sql_text.clear()
            return

        columns, rows = self.db.get_view_rows(view_name)
        self.current_view_columns = columns
        self.all_view_rows = rows
        self.view_sql_text.setPlainText(self.db.get_object_sql(view_name))
        self.filter_view_rows()

    def filter_view_rows(self) -> None:
        search_text = self.view_search_edit.text().strip().lower()
        if not search_text:
            self.current_view_rows = list(self.all_view_rows)
        else:
            self.current_view_rows = [
                row
                for row in self.all_view_rows
                if search_text in " ".join(str(value).lower() for value in row.values())
            ]
        self.fill_table(self.view_table, self.current_view_rows, self.current_view_columns)

    def fill_table(self, table: QtWidgets.QTableWidget, rows, columns) -> None:
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(len(columns))
        if columns:
            table.setHorizontalHeaderLabels(columns)
        if not columns:
            return

        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, column in enumerate(columns):
                value = row.get(column, "")
                item = QtWidgets.QTableWidgetItem(self._format_cell_value(value))
                if self._is_number(value):
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                table.setItem(row_index, col_index, item)

        table.resizeColumnsToContents()

    def selected_row(self, table: QtWidgets.QTableWidget, rows):
        row_index = table.currentRow()
        if row_index < 0 or row_index >= len(rows):
            return None
        return rows[row_index]

    def add_television(self) -> None:
        dialog = TelevisionDialog(self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        try:
            self.db.add_television(dialog.get_data())
            self.refresh_after_write("Телевизор добавлен.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def edit_television(self) -> None:
        if not self.user.can_edit:
            return
        row = self.selected_row(self.television_table, self.television_rows)
        if not row:
            QtWidgets.QMessageBox.information(self, "Подсказка", "Выберите телевизор в таблице.")
            return
        dialog = TelevisionDialog(self, row)
        dialog.tv_code_spin.setEnabled(False)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        try:
            self.db.update_television(int(row["tv_code"]), dialog.get_data())
            self.refresh_after_write("Данные телевизора обновлены.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def delete_television(self) -> None:
        if not self.user.can_delete:
            return
        row = self.selected_row(self.television_table, self.television_rows)
        if not row:
            QtWidgets.QMessageBox.information(self, "Подсказка", "Выберите телевизор в таблице.")
            return
        answer = QtWidgets.QMessageBox.question(
            self,
            "Подтверждение удаления",
            f'Удалить телевизор с кодом {row["tv_code"]}?',
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.db.delete_television(int(row["tv_code"]))
            self.refresh_after_write("Телевизор удален.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def add_order(self) -> None:
        dialog = ClientDialog(self.db.television_choices(), self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        try:
            self.db.add_order(dialog.get_data())
            self.refresh_after_write("Заказ добавлен.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def edit_order(self) -> None:
        if not self.user.can_edit:
            return
        row = self.selected_row(self.order_table, self.order_rows)
        if not row:
            QtWidgets.QMessageBox.information(self, "Подсказка", "Выберите заказ в таблице.")
            return

        dialog_data = self.db.get_order_dialog_data(int(row["order_number"]))
        if not dialog_data:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные заказа.")
            return

        dialog = ClientDialog(self.db.television_choices(), self, dialog_data)
        dialog.order_number_spin.setEnabled(False)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        try:
            self.db.update_order(int(row["order_number"]), dialog.get_data())
            self.refresh_after_write("Заказ обновлен.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def delete_order(self) -> None:
        if not self.user.can_delete:
            return
        row = self.selected_row(self.order_table, self.order_rows)
        if not row:
            QtWidgets.QMessageBox.information(self, "Подсказка", "Выберите заказ в таблице.")
            return
        answer = QtWidgets.QMessageBox.question(
            self,
            "Подтверждение удаления",
            f'Удалить заказ № {row["order_number"]}?',
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.db.delete_order(int(row["order_number"]))
            self.refresh_after_write("Заказ удален.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(exc))

    def refresh_after_write(self, message: str) -> None:
        self.refresh_reference_data()
        self.refresh_dashboard()
        self.load_televisions()
        self.load_customers()
        self.load_orders()
        self.load_current_view()
        self.statusBar().showMessage(message, 5000)

    def export_view_to_csv(self) -> None:
        if not self.current_view_columns:
            return
        view_name = self.view_combo.currentText().strip() or "view"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            str(Path.cwd() / f"{view_name}.csv"),
            "CSV (*.csv)",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(self.current_view_columns)
                for row in self.current_view_rows:
                    writer.writerow([row.get(column, "") for column in self.current_view_columns])
            self.statusBar().showMessage(f"CSV сохранен: {path}", 5000)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка экспорта", str(exc))

    def closeEvent(self, event) -> None:
        self.db.close()
        super().closeEvent(event)

    @staticmethod
    def _format_cell_value(value) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            return f"{value:,.2f}".replace(",", " ")
        return str(value)

    @staticmethod
    def _is_number(value) -> bool:
        return isinstance(value, (int, float))
