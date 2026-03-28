from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets


class TelevisionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Телевизор")
        self.resize(560, 460)

        self.image_data = self._normalize_image_bytes(data.get("image_data")) if data else b""
        self.image_filename = str(data.get("image_filename") or "").strip() if data else ""

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.tv_code_spin = QtWidgets.QSpinBox()
        self.tv_code_spin.setMaximum(999999)

        self.model_edit = QtWidgets.QLineEdit()
        self.model_edit.setPlaceholderText("Например, Samsung UE43DU7100")

        self.manufacturer_edit = QtWidgets.QLineEdit()
        self.manufacturer_edit.setPlaceholderText("Например, Samsung")

        self.diagonal_spin = QtWidgets.QSpinBox()
        self.diagonal_spin.setRange(32, 500)

        self.price_spin = QtWidgets.QDoubleSpinBox()
        self.price_spin.setRange(0, 99999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setSingleStep(1000)
        self.price_spin.setSuffix(" руб.")

        self.discount_spin = QtWidgets.QSpinBox()
        self.discount_spin.setRange(0, 100)

        self.image_preview_label = QtWidgets.QLabel("Изображение не выбрано")
        self.image_preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_preview_label.setMinimumSize(260, 160)
        self.image_preview_label.setFrameShape(QtWidgets.QFrame.Box)

        self.image_name_label = QtWidgets.QLabel("Будет создано автоматически")
        self.image_name_label.setWordWrap(True)

        self.choose_image_button = QtWidgets.QPushButton("Выбрать файл")
        self.clear_image_button = QtWidgets.QPushButton("Очистить")

        image_controls = QtWidgets.QHBoxLayout()
        image_controls.addWidget(self.choose_image_button)
        image_controls.addWidget(self.clear_image_button)
        image_controls.addStretch(1)

        image_widget = QtWidgets.QWidget()
        image_layout = QtWidgets.QVBoxLayout(image_widget)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(8)
        image_layout.addWidget(self.image_preview_label)
        image_layout.addWidget(self.image_name_label)
        image_layout.addLayout(image_controls)

        layout.addRow("Код телевизора:", self.tv_code_spin)
        layout.addRow("Модель:", self.model_edit)
        layout.addRow("Производитель:", self.manufacturer_edit)
        layout.addRow("Диагональ (см):", self.diagonal_spin)
        layout.addRow("Цена:", self.price_spin)
        layout.addRow("Скидка (%):", self.discount_spin)
        layout.addRow("Изображение:", image_widget)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.choose_image_button.clicked.connect(self.choose_image_file)
        self.clear_image_button.clicked.connect(self.clear_image)

        if data:
            self.tv_code_spin.setValue(int(data.get("tv_code", 0)))
            self.model_edit.setText(str(data.get("model_name", "")))
            self.manufacturer_edit.setText(str(data.get("manufacturer", "")))
            self.diagonal_spin.setValue(int(data.get("diagonal_cm", 32)))
            self.price_spin.setValue(float(data.get("price", 0)))
            self.discount_spin.setValue(int(data.get("discount_percent", 0)))

        self.update_image_preview()

    def choose_image_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите изображение телевизора",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.webp);;Все файлы (*)",
        )
        if not path:
            return

        try:
            self.image_data = Path(path).read_bytes()
            self.image_filename = Path(path).name
            self.update_image_preview()
        except OSError as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {exc}")

    def clear_image(self) -> None:
        self.image_data = b""
        self.image_filename = ""
        self.update_image_preview()

    def update_image_preview(self) -> None:
        if self.image_data:
            pixmap = QtGui.QPixmap()
            if pixmap.loadFromData(self.image_data):
                scaled = pixmap.scaled(
                    260,
                    160,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
                self.image_preview_label.setPixmap(scaled)
                self.image_preview_label.setText("")
                self.image_name_label.setText(self.image_filename or "Изображение из базы")
                return

        self.image_preview_label.setPixmap(QtGui.QPixmap())
        self.image_preview_label.setText("Будет создано автоматически")
        self.image_name_label.setText("При сохранении приложение создаст изображение по данным модели")

    def accept(self) -> None:
        if not self.model_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите название модели.")
            return
        if not self.manufacturer_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите производителя.")
            return
        super().accept()

    def get_data(self) -> dict:
        return {
            "tv_code": self.tv_code_spin.value(),
            "model_name": self.model_edit.text().strip(),
            "manufacturer": self.manufacturer_edit.text().strip(),
            "diagonal_cm": self.diagonal_spin.value(),
            "price": self.price_spin.value(),
            "discount_percent": self.discount_spin.value(),
            "image_data": self.image_data,
            "image_filename": self.image_filename,
        }

    @staticmethod
    def _normalize_image_bytes(value) -> bytes:
        if isinstance(value, memoryview):
            value = value.tobytes()
        if isinstance(value, bytearray):
            value = bytes(value)
        if isinstance(value, bytes):
            return value
        return b""


class ClientDialog(QtWidgets.QDialog):
    def __init__(self, television_choices, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Заказ")
        self.resize(520, 360)

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.order_number_spin = QtWidgets.QSpinBox()
        self.order_number_spin.setMaximum(999999)

        self.tv_combo = QtWidgets.QComboBox()
        self.tv_combo.setMinimumWidth(280)
        for tv_code, label in television_choices:
            self.tv_combo.addItem(label, tv_code)

        self.full_name_edit = QtWidgets.QLineEdit()
        self.full_name_edit.setPlaceholderText("Фамилия Имя Отчество")

        self.order_date_edit = QtWidgets.QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.order_date_edit.setDate(QtCore.QDate.currentDate())

        self.quantity_spin = QtWidgets.QSpinBox()
        self.quantity_spin.setRange(1, 9999)

        self.place_edit = QtWidgets.QLineEdit()
        self.place_edit.setPlaceholderText("Город доставки")

        self.discount_spin = QtWidgets.QSpinBox()
        self.discount_spin.setRange(0, 100)

        layout.addRow("Номер заказа:", self.order_number_spin)
        layout.addRow("Телевизор:", self.tv_combo)
        layout.addRow("ФИО клиента:", self.full_name_edit)
        layout.addRow("Дата заказа:", self.order_date_edit)
        layout.addRow("Количество:", self.quantity_spin)
        layout.addRow("Город:", self.place_edit)
        layout.addRow("Скидка клиента (%):", self.discount_spin)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        if data:
            self.order_number_spin.setValue(int(data.get("order_number", 0)))
            self.full_name_edit.setText(str(data.get("full_name", "")))
            order_date = QtCore.QDate.fromString(str(data.get("order_date", "")), "yyyy-MM-dd")
            if order_date.isValid():
                self.order_date_edit.setDate(order_date)
            self.quantity_spin.setValue(int(data.get("quantity", 1)))
            self.place_edit.setText(str(data.get("place", "")))
            self.discount_spin.setValue(int(data.get("discount_percent", 0)))
            tv_code = int(data.get("tv_code", 0))
            index = self.tv_combo.findData(tv_code)
            if index >= 0:
                self.tv_combo.setCurrentIndex(index)

    def accept(self) -> None:
        if self.tv_combo.count() == 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка",
                "В таблице televisions нет записей. Сначала добавьте телевизор.",
            )
            return
        if not self.full_name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите ФИО клиента.")
            return
        if not self.place_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите город доставки.")
            return
        super().accept()

    def get_data(self) -> dict:
        return {
            "order_number": self.order_number_spin.value(),
            "tv_code": int(self.tv_combo.currentData()),
            "full_name": self.full_name_edit.text().strip(),
            "order_date": self.order_date_edit.date().toString("yyyy-MM-dd"),
            "quantity": self.quantity_spin.value(),
            "place": self.place_edit.text().strip(),
            "discount_percent": self.discount_spin.value(),
        }
