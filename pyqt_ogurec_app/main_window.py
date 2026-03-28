import csv
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from pyqt_ogurec_app.config import APP_TITLE, resolve_default_db_path
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
        self.resize(1280, 860)

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

        root_layout.addWidget(self._build_database_group(), 0, 0)
        root_layout.addWidget(self._build_tables_group(), 1, 0)
        root_layout.addWidget(self._build_views_group(), 2, 0)

        root_layout.setRowStretch(1, 3)
        root_layout.setRowStretch(2, 3)

        self.stats_label = QtWidgets.QLabel("")
        self.statusBar().addPermanentWidget(self.stats_label)
        self.statusBar().showMessage("Готово к работе")

    def _build_tables_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Таблицы базы")
        layout = QtWidgets.QVBoxLayout(group)

        selector_row = QtWidgets.QHBoxLayout()
        selector_row.addWidget(QtWidgets.QLabel("Показать таблицу:"))
        self.table_selector = QtWidgets.QComboBox()
        self.table_selector.addItem("Телевизоры", "televisions")
        self.table_selector.addItem("Клиенты", "customers")
        self.table_selector.addItem("Заказы", "orders")
        selector_row.addWidget(self.table_selector)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)

        self.table_stack = QtWidgets.QStackedWidget()
        self.table_stack.addWidget(self._build_televisions_group())
        self.table_stack.addWidget(self._build_customers_group())
        self.table_stack.addWidget(self._build_orders_group())
        layout.addWidget(self.table_stack, stretch=1)
        return group

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

        layout.addWidget(
            QtWidgets.QLabel("Структура базы: televisions, customers, orders"),
            1,
            0,
            1,
            4,
        )
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

        content_layout = QtWidgets.QHBoxLayout()
        self.television_table = self._create_table_widget()
        content_layout.addWidget(self.television_table, stretch=3)
        (
            tv_preview_group,
            self.tv_preview_title,
            self.tv_image_label,
            self.tv_preview_details,
        ) = self._build_image_preview_group("Изображение телевизора")
        content_layout.addWidget(tv_preview_group, stretch=2)
        layout.addLayout(content_layout, stretch=1)
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
        self.order_search_edit.setPlaceholderText("Номер заказа, клиент, tv_code или дата")
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

        content_layout = QtWidgets.QHBoxLayout()
        self.order_table = self._create_table_widget()
        content_layout.addWidget(self.order_table, stretch=3)
        (
            order_preview_group,
            self.order_preview_title,
            self.order_image_label,
            self.order_preview_details,
        ) = self._build_image_preview_group("Изображение по заказу")
        content_layout.addWidget(order_preview_group, stretch=2)
        layout.addLayout(content_layout, stretch=1)
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

    def _build_image_preview_group(self, title: str):
        group = QtWidgets.QGroupBox(title)
        group.setMinimumWidth(320)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(10)

        title_label = QtWidgets.QLabel("Выберите запись в таблице")
        title_label.setWordWrap(True)

        image_label = QtWidgets.QLabel("Нет изображения")
        image_label.setAlignment(QtCore.Qt.AlignCenter)
        image_label.setMinimumSize(300, 220)
        image_label.setFrameShape(QtWidgets.QFrame.Box)

        details_label = QtWidgets.QLabel("")
        details_label.setWordWrap(True)
        details_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        layout.addWidget(title_label)
        layout.addWidget(image_label, stretch=1)
        layout.addWidget(details_label)
        return group, title_label, image_label, details_label

    def _create_table_widget(self) -> QtWidgets.QTableWidget:
        return DataTable()

    def _connect_signals(self) -> None:
        self.browse_db_button.clicked.connect(self.choose_database_file)
        self.reconnect_button.clicked.connect(self.connect_database)
        self.table_selector.currentIndexChanged.connect(self.change_table_page)

        self.tv_search_edit.textChanged.connect(self.load_televisions)
        self.tv_manufacturer_combo.currentTextChanged.connect(self.load_televisions)
        self.tv_discount_spin.valueChanged.connect(self.load_televisions)
        self.tv_sort_combo.currentIndexChanged.connect(self.load_televisions)
        self.refresh_tv_button.clicked.connect(self.load_televisions)
        self.add_tv_button.clicked.connect(self.add_television)
        self.edit_tv_button.clicked.connect(self.edit_television)
        self.delete_tv_button.clicked.connect(self.delete_television)
        self.television_table.itemDoubleClicked.connect(lambda *_: self.edit_television())
        self.television_table.itemSelectionChanged.connect(self.update_television_preview)

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
        self.order_table.itemSelectionChanged.connect(self.update_order_preview)

        self.view_combo.currentTextChanged.connect(self.load_current_view)
        self.view_search_edit.textChanged.connect(self.filter_view_rows)
        self.refresh_view_button.clicked.connect(self.load_current_view)
        self.export_view_button.clicked.connect(self.export_view_to_csv)

    def change_table_page(self, index: int) -> None:
        self.table_stack.setCurrentIndex(max(index, 0))
        table_name = self.table_selector.itemData(max(index, 0))
        if table_name == "televisions":
            self.update_television_preview()
        elif table_name == "orders":
            self.update_order_preview()

    def _apply_permissions(self) -> None:
        self.add_tv_button.setEnabled(self.user.can_add)
        self.edit_tv_button.setEnabled(self.user.can_edit)
        self.delete_tv_button.setEnabled(self.user.can_delete)
        self.add_order_button.setEnabled(self.user.can_add)
        self.edit_order_button.setEnabled(self.user.can_edit)
        self.delete_order_button.setEnabled(self.user.can_delete)

    def choose_database_file(self) -> None:
        current_path = Path(self.db_path_edit.text().strip() or resolve_default_db_path())
        start_dir = current_path.parent if current_path.suffix else current_path
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите файл базы данных",
            str(start_dir),
            "SQLite (*.db *.sqlite *.sqlite3);;Все файлы (*)",
        )
        if path:
            self.db_path_edit.setText(path)
            self.connect_database()

    def connect_database(self, initial: bool = False) -> None:
        path = self.db_path_edit.text().strip() or resolve_default_db_path()
        if not path:
            if not initial:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Укажите путь к файлу базы данных.")
            return
        try:
            self.db.set_path(path)
            path = self.db.db_path
            self.db_path_edit.setText(self.db.db_path)
            self.refresh_reference_data()
            self.refresh_dashboard()
            self.load_televisions()
            self.load_customers()
            self.load_orders()
            self.load_current_view()
            db_name = Path(self.db.db_path).name
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

        selected_row = self.selected_row(self.television_table, self.television_rows)
        selected_tv_code = selected_row["tv_code"] if selected_row else None

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
        self._restore_selection(self.television_table, self.television_rows, "tv_code", selected_tv_code)

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

        selected_row = self.selected_row(self.order_table, self.order_rows)
        selected_order_number = selected_row["order_number"] if selected_row else None

        self.order_rows = self.db.get_orders(
            search=self.order_search_edit.text().strip(),
            sort_mode=self.order_sort_combo.currentData(),
        )
        self.fill_table(
            self.order_table,
            self.order_rows,
            ["order_number", "customer_id", "tv_code", "order_date", "quantity", "discount_percent"],
        )
        self._restore_selection(self.order_table, self.order_rows, "order_number", selected_order_number)

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

    def _restore_selection(self, table: QtWidgets.QTableWidget, rows, key: str, selected_value) -> None:
        if not rows:
            table.clearSelection()
            if table is self.television_table:
                self.clear_television_preview()
            elif table is self.order_table:
                self.clear_order_preview()
            return

        target_index = 0
        if selected_value is not None:
            for index, row in enumerate(rows):
                if row.get(key) == selected_value:
                    target_index = index
                    break

        table.setCurrentCell(target_index, 0)
        table.selectRow(target_index)

    def update_television_preview(self) -> None:
        row = self.selected_row(self.television_table, self.television_rows)
        if not row:
            self.clear_television_preview()
            return

        title = f'{row["manufacturer"]} {row["model_name"]}'
        details = (
            f'Код: {row["tv_code"]}\n'
            f'Диагональ: {row["diagonal_cm"]} см\n'
            f'Цена: {self._format_price(row["price"])} руб.\n'
            f'Скидка: {row["discount_percent"]}%'
        )
        self.set_preview_content(
            self.tv_preview_title,
            self.tv_image_label,
            self.tv_preview_details,
            title,
            details,
            row.get("image_data"),
        )

    def clear_television_preview(self) -> None:
        self.clear_preview_content(
            self.tv_preview_title,
            self.tv_image_label,
            self.tv_preview_details,
            "Выберите телевизор в таблице",
        )

    def update_order_preview(self) -> None:
        row = self.selected_row(self.order_table, self.order_rows)
        if not row:
            self.clear_order_preview()
            return

        title = f'Заказ № {row["order_number"]}'
        details = (
            f'Клиент: {row.get("customer_name", "")}\n'
            f'Телевизор: {row.get("tv_manufacturer", "")} {row.get("tv_model_name", "")}\n'
            f'Дата: {row["order_date"]}\n'
            f'Количество: {row["quantity"]}\n'
            f'Скидка клиента: {row["discount_percent"]}%'
        )
        self.set_preview_content(
            self.order_preview_title,
            self.order_image_label,
            self.order_preview_details,
            title,
            details,
            row.get("image_data"),
        )

    def clear_order_preview(self) -> None:
        self.clear_preview_content(
            self.order_preview_title,
            self.order_image_label,
            self.order_preview_details,
            "Выберите заказ в таблице",
        )

    def set_preview_content(
        self,
        title_label: QtWidgets.QLabel,
        image_label: QtWidgets.QLabel,
        details_label: QtWidgets.QLabel,
        title: str,
        details: str,
        image_data,
    ) -> None:
        title_label.setText(title)
        details_label.setText(details)

        raw_data = self._normalize_image_bytes(image_data)
        pixmap = QtGui.QPixmap()
        if raw_data and pixmap.loadFromData(raw_data):
            target_size = image_label.size()
            if target_size.width() < 120 or target_size.height() < 120:
                target_size = QtCore.QSize(300, 220)
            image_label.setPixmap(
                pixmap.scaled(
                    target_size,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
            )
            image_label.setText("")
            return

        image_label.setPixmap(QtGui.QPixmap())
        image_label.setText("Нет изображения")

    def clear_preview_content(
        self,
        title_label: QtWidgets.QLabel,
        image_label: QtWidgets.QLabel,
        details_label: QtWidgets.QLabel,
        empty_title: str,
    ) -> None:
        title_label.setText(empty_title)
        details_label.clear()
        image_label.setPixmap(QtGui.QPixmap())
        image_label.setText("Нет изображения")

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
        default_dir = Path(self.db.db_path).parent if self.db.db_path else Path.cwd()
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            str(default_dir / f"{view_name}.csv"),
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
    def _normalize_image_bytes(value) -> bytes:
        if isinstance(value, memoryview):
            value = value.tobytes()
        if isinstance(value, bytearray):
            value = bytes(value)
        if isinstance(value, bytes):
            return value
        return b""

    @staticmethod
    def _format_price(value) -> str:
        return f"{float(value):,.0f}".replace(",", " ")

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
