import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from PyQt5 import QtCore, QtGui, QtWidgets


ALL_MANUFACTURERS = "Все производители"
ALL_PLACES = "Все города"
HIDDEN_VIEWS = {"clients"}
DEFAULT_IMAGE_SIZE = QtCore.QSize(420, 340)
_IMAGE_APP = None


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self.connection:
            self.connection.close()
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"Файл базы данных не найден: {db_file}")
        self.connection = sqlite3.connect(str(db_file), timeout=5)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self._ensure_television_image_columns()
        self._populate_missing_television_images()

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def set_path(self, db_path: str) -> None:
        self.db_path = db_path
        self.connect()

    def query(self, sql: str, params: Iterable = ()) -> list[sqlite3.Row]:
        cursor = self._require_connection().cursor()
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()

    def execute(self, sql: str, params: Iterable = ()) -> None:
        cursor = self._require_connection().cursor()
        cursor.execute(sql, tuple(params))
        self.connection.commit()

    def scalar(self, sql: str, params: Iterable = ()):
        cursor = self._require_connection().cursor()
        cursor.execute(sql, tuple(params))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def object_names(self) -> list[tuple[str, str]]:
        rows = self.query(
            """
            SELECT name, type
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY CASE WHEN type = 'table' THEN 0 ELSE 1 END, name
            """
        )
        return [(row["name"], row["type"]) for row in rows]

    def list_views(self) -> list[str]:
        return [
            name
            for name, kind in self.object_names()
            if kind == "view" and name not in HIDDEN_VIEWS
        ]

    def list_manufacturers(self) -> list[str]:
        rows = self.query(
            """
            SELECT DISTINCT manufacturer
            FROM televisions
            ORDER BY manufacturer
            """
        )
        return [row["manufacturer"] for row in rows]

    def list_places(self) -> list[str]:
        rows = self.query(
            """
            SELECT DISTINCT place
            FROM customers
            ORDER BY place
            """
        )
        return [row["place"] for row in rows]

    def get_televisions(
        self,
        search: str = "",
        manufacturer: str = "",
        min_discount: int = 0,
        sort_mode: str = "price_desc",
    ) -> list[dict]:
        sql = """
            SELECT
                tv_code,
                model_name,
                manufacturer,
                diagonal_cm,
                price,
                discount_percent,
                image_data,
                image_filename
            FROM televisions
            WHERE 1 = 1
        """
        params: list = []
        if search:
            sql += """
                AND (
                    CAST(tv_code AS TEXT) LIKE ?
                    OR model_name LIKE ?
                    OR manufacturer LIKE ?
                )
            """
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])
        if manufacturer and manufacturer != ALL_MANUFACTURERS:
            sql += " AND manufacturer = ?"
            params.append(manufacturer)
        sql += " AND discount_percent >= ?"
        params.append(min_discount)

        sort_sql = {
            "price_desc": " ORDER BY price DESC, model_name",
            "price_asc": " ORDER BY price ASC, model_name",
            "discount_desc": " ORDER BY discount_percent DESC, model_name",
            "model_asc": " ORDER BY model_name ASC",
        }
        sql += sort_sql.get(sort_mode, sort_sql["price_desc"])
        return [dict(row) for row in self.query(sql, params)]

    def get_customers(
        self,
        search: str = "",
        place: str = "",
        sort_mode: str = "name_asc",
    ) -> list[dict]:
        sql = """
            SELECT
                customer_id,
                full_name,
                place
            FROM customers
            WHERE 1 = 1
        """
        params: list = []
        if search:
            pattern = f"%{search.strip()}%"
            sql += """
                AND (
                    CAST(customer_id AS TEXT) LIKE ?
                    OR full_name LIKE ?
                    OR place LIKE ?
                )
            """
            params.extend([pattern, pattern, pattern])
        if place and place != ALL_PLACES:
            sql += " AND place = ?"
            params.append(place)

        sort_sql = {
            "name_asc": " ORDER BY full_name ASC, customer_id ASC",
            "place_asc": " ORDER BY place ASC, full_name ASC",
            "id_asc": " ORDER BY customer_id ASC",
            "id_desc": " ORDER BY customer_id DESC",
        }
        sql += sort_sql.get(sort_mode, sort_sql["name_asc"])
        return [dict(row) for row in self.query(sql, params)]

    def get_orders(
        self,
        search: str = "",
        sort_mode: str = "date_desc",
    ) -> list[dict]:
        sql = """
            SELECT
                o.order_number,
                o.customer_id,
                o.tv_code,
                o.order_date,
                o.quantity,
                o.discount_percent,
                c.full_name AS customer_name,
                c.place AS customer_place,
                t.model_name AS tv_model_name,
                t.manufacturer AS tv_manufacturer,
                t.image_data,
                t.image_filename
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN televisions t ON t.tv_code = o.tv_code
            WHERE 1 = 1
        """
        params: list = []
        if search:
            pattern = f"%{search.strip()}%"
            sql += """
                AND (
                    CAST(o.order_number AS TEXT) LIKE ?
                    OR CAST(o.customer_id AS TEXT) LIKE ?
                    OR CAST(o.tv_code AS TEXT) LIKE ?
                    OR o.order_date LIKE ?
                    OR c.full_name LIKE ?
                    OR t.model_name LIKE ?
                )
            """
            params.extend([pattern, pattern, pattern, pattern, pattern, pattern])

        sort_sql = {
            "date_desc": " ORDER BY o.order_date DESC, o.order_number DESC",
            "date_asc": " ORDER BY o.order_date ASC, o.order_number ASC",
            "order_asc": " ORDER BY o.order_number ASC",
            "quantity_desc": " ORDER BY o.quantity DESC, o.order_number DESC",
        }
        sql += sort_sql.get(sort_mode, sort_sql["date_desc"])
        return [dict(row) for row in self.query(sql, params)]

    def get_view_rows(self, view_name: str) -> tuple[list[str], list[dict]]:
        if view_name not in self.list_views():
            raise ValueError(f"Представление {view_name} не найдено в базе.")
        rows = self.query(f'SELECT * FROM "{view_name}"')
        if not rows:
            return self.get_columns(view_name), []
        return list(rows[0].keys()), [dict(row) for row in rows]

    def get_columns(self, object_name: str) -> list[str]:
        rows = self.query(f'PRAGMA table_info("{object_name}")')
        return [row["name"] for row in rows]

    def get_object_sql(self, object_name: str) -> str:
        rows = self.query(
            """
            SELECT sql
            FROM sqlite_master
            WHERE name = ?
              AND type IN ('table', 'view')
            """,
            [object_name],
        )
        if not rows:
            return ""
        return rows[0]["sql"] or ""

    def television_choices(self) -> list[tuple[int, str]]:
        rows = self.query(
            """
            SELECT tv_code, model_name, manufacturer
            FROM televisions
            ORDER BY manufacturer, model_name
            """
        )
        return [
            (row["tv_code"], f'{row["tv_code"]} - {row["manufacturer"]} {row["model_name"]}')
            for row in rows
        ]

    def get_television(self, tv_code: int) -> Optional[dict]:
        rows = self.query("SELECT * FROM televisions WHERE tv_code = ?", [tv_code])
        return dict(rows[0]) if rows else None

    def get_order_dialog_data(self, order_number: int) -> Optional[dict]:
        rows = self.query(
            """
            SELECT
                o.order_number,
                o.tv_code,
                c.full_name,
                o.order_date,
                o.quantity,
                c.place,
                o.discount_percent
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_number = ?
            """,
            [order_number],
        )
        return dict(rows[0]) if rows else None

    def add_television(self, data: dict) -> None:
        image_data, image_filename = self._prepare_television_image_payload(data)
        self.execute(
            """
            INSERT INTO televisions (
                tv_code,
                model_name,
                manufacturer,
                diagonal_cm,
                price,
                discount_percent,
                image_data,
                image_filename
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                data["tv_code"],
                data["model_name"],
                data["manufacturer"],
                data["diagonal_cm"],
                data["price"],
                data["discount_percent"],
                image_data,
                image_filename,
            ],
        )

    def update_television(self, tv_code: int, data: dict) -> None:
        image_data, image_filename = self._prepare_television_image_payload(data, tv_code)
        self.execute(
            """
            UPDATE televisions
            SET model_name = ?,
                manufacturer = ?,
                diagonal_cm = ?,
                price = ?,
                discount_percent = ?,
                image_data = ?,
                image_filename = ?
            WHERE tv_code = ?
            """,
            [
                data["model_name"],
                data["manufacturer"],
                data["diagonal_cm"],
                data["price"],
                data["discount_percent"],
                image_data,
                image_filename,
                tv_code,
            ],
        )

    def delete_television(self, tv_code: int) -> None:
        self.execute("DELETE FROM televisions WHERE tv_code = ?", [tv_code])

    def add_order(self, data: dict) -> None:
        connection = self._require_connection()
        cursor = connection.cursor()
        try:
            customer_id = self._get_or_create_customer(
                cursor,
                data["full_name"],
                data["place"],
            )
            cursor.execute(
                """
                INSERT INTO orders (
                    order_number, customer_id, tv_code, order_date, quantity, discount_percent
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    data["order_number"],
                    customer_id,
                    data["tv_code"],
                    data["order_date"],
                    data["quantity"],
                    data["discount_percent"],
                ],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def update_order(self, order_number: int, data: dict) -> None:
        connection = self._require_connection()
        cursor = connection.cursor()
        try:
            row = cursor.execute(
                "SELECT customer_id FROM orders WHERE order_number = ?",
                [order_number],
            ).fetchone()
            if row is None:
                raise ValueError(f"Заказ №{order_number} не найден.")

            previous_customer_id = row[0]
            customer_id = self._get_or_create_customer(
                cursor,
                data["full_name"],
                data["place"],
            )
            cursor.execute(
                """
                UPDATE orders
                SET customer_id = ?, tv_code = ?, order_date = ?, quantity = ?, discount_percent = ?
                WHERE order_number = ?
                """,
                [
                    customer_id,
                    data["tv_code"],
                    data["order_date"],
                    data["quantity"],
                    data["discount_percent"],
                    order_number,
                ],
            )
            self._delete_orphan_customer(cursor, previous_customer_id)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def delete_order(self, order_number: int) -> None:
        connection = self._require_connection()
        cursor = connection.cursor()
        try:
            row = cursor.execute(
                "SELECT customer_id FROM orders WHERE order_number = ?",
                [order_number],
            ).fetchone()
            if row is None:
                return

            customer_id = row[0]
            cursor.execute("DELETE FROM orders WHERE order_number = ?", [order_number])
            self._delete_orphan_customer(cursor, customer_id)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def dashboard_stats(self) -> dict:
        television_count = self.scalar("SELECT COUNT(*) FROM televisions") or 0
        customer_count = self.scalar("SELECT COUNT(*) FROM customers") or 0
        order_count = self.scalar("SELECT COUNT(*) FROM orders") or 0
        view_count = self.scalar(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'view'
              AND name NOT LIKE 'sqlite_%'
              AND name NOT IN ('clients')
            """
        ) or 0
        return {
            "television_count": television_count,
            "customer_count": customer_count,
            "order_count": order_count,
            "view_count": view_count,
        }

    def _ensure_television_image_columns(self) -> None:
        columns = {row["name"] for row in self.query('PRAGMA table_info("televisions")')}
        schema_changed = False

        if "image_data" not in columns:
            self.connection.execute("ALTER TABLE televisions ADD COLUMN image_data BLOB")
            schema_changed = True
        if "image_filename" not in columns:
            self.connection.execute("ALTER TABLE televisions ADD COLUMN image_filename TEXT")
            schema_changed = True

        if schema_changed:
            self.connection.commit()

    def _populate_missing_television_images(self) -> None:
        rows = self.query(
            """
            SELECT
                tv_code,
                model_name,
                manufacturer,
                diagonal_cm,
                price,
                discount_percent,
                image_data,
                image_filename
            FROM televisions
            WHERE image_data IS NULL
               OR length(image_data) = 0
               OR image_filename IS NULL
               OR image_filename = ''
            """
        )
        if not rows:
            return

        cursor = self._require_connection().cursor()
        for row in rows:
            image_data, image_filename = self._prepare_television_image_payload(dict(row), row["tv_code"])
            cursor.execute(
                """
                UPDATE televisions
                SET image_data = ?, image_filename = ?
                WHERE tv_code = ?
                """,
                [image_data, image_filename, row["tv_code"]],
            )
        self.connection.commit()

    def _prepare_television_image_payload(
        self,
        data: dict,
        tv_code: Optional[int] = None,
    ) -> tuple[sqlite3.Binary, str]:
        raw_data = self._normalize_image_bytes(data.get("image_data"))
        actual_tv_code = tv_code if tv_code is not None else int(data.get("tv_code", 0))
        image_filename = str(data.get("image_filename") or "").strip()

        if not raw_data:
            raw_data, image_filename = self._build_default_television_image(data, actual_tv_code)
        elif not image_filename:
            image_filename = f"television_{actual_tv_code or 'image'}.png"

        return sqlite3.Binary(raw_data), image_filename

    def _build_default_television_image(
        self,
        data: dict,
        tv_code: int,
    ) -> tuple[bytes, str]:
        self._ensure_image_application()
        manufacturer = str(data.get("manufacturer", "TV")).strip() or "TV"
        model_name = str(data.get("model_name", "Модель")).strip() or "Модель"
        diagonal_cm = int(data.get("diagonal_cm", 0) or 0)
        price = float(data.get("price", 0) or 0)
        discount_percent = int(data.get("discount_percent", 0) or 0)

        image = QtGui.QImage(DEFAULT_IMAGE_SIZE, QtGui.QImage.Format_ARGB32)
        image.fill(QtGui.QColor("#f2f5fb"))

        accent = self._accent_color(manufacturer)
        dark = QtGui.QColor("#1e2430")
        light = QtGui.QColor("#ffffff")
        muted = QtGui.QColor("#5d6677")

        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        header_rect = QtCore.QRect(0, 0, image.width(), 70)
        painter.fillRect(header_rect, accent)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(255, 255, 255, 30))
        painter.drawEllipse(QtCore.QRect(300, -30, 120, 120))
        painter.drawEllipse(QtCore.QRect(250, 10, 80, 80))

        screen_rect = QtCore.QRect(38, 92, 344, 118)
        painter.setBrush(dark)
        painter.setPen(QtGui.QPen(QtGui.QColor("#0f131a"), 2))
        painter.drawRoundedRect(screen_rect, 10, 10)

        inner_rect = screen_rect.adjusted(10, 10, -10, -10)
        painter.setBrush(QtGui.QColor("#101828"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(inner_rect, 6, 6)

        painter.setBrush(QtGui.QColor(255, 255, 255, 28))
        painter.drawRect(inner_rect.adjusted(16, 12, -90, -48))

        painter.setPen(QtGui.QPen(QtGui.QColor("#d4dbe7"), 4))
        painter.drawLine(170, 212, 250, 212)
        painter.drawLine(206, 212, 188, 234)
        painter.drawLine(214, 212, 232, 234)

        painter.setPen(light)
        painter.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRect(24, 16, 220, 24), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, manufacturer)

        painter.setPen(QtGui.QColor("#d7deea"))
        painter.setFont(QtGui.QFont("Segoe UI", 9))
        painter.drawText(
            QtCore.QRect(24, 40, 260, 20),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            f"Код телевизора: {tv_code}",
        )

        painter.setPen(dark)
        painter.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
        painter.drawText(
            QtCore.QRect(28, 236, 360, 28),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            model_name,
        )

        painter.setPen(muted)
        painter.setFont(QtGui.QFont("Segoe UI", 10))
        painter.drawText(
            QtCore.QRect(28, 266, 185, 20),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            f"Диагональ: {diagonal_cm} см",
        )
        painter.drawText(
            QtCore.QRect(220, 266, 164, 20),
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
            f"Скидка: {discount_percent}%",
        )

        painter.setPen(accent.darker(110))
        painter.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        painter.drawText(
            QtCore.QRect(28, 292, 360, 28),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            f"{price:,.0f} руб.".replace(",", " "),
        )

        painter.end()

        byte_array = QtCore.QByteArray()
        buffer = QtCore.QBuffer(byte_array)
        buffer.open(QtCore.QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        return bytes(byte_array), f"television_{tv_code}.png"

    def _accent_color(self, manufacturer: str) -> QtGui.QColor:
        palette = [
            "#3563e9",
            "#0f766e",
            "#d97706",
            "#dc2626",
            "#7c3aed",
            "#2563eb",
            "#0ea5a4",
            "#ca8a04",
        ]
        index = sum(ord(char) for char in manufacturer) % len(palette)
        return QtGui.QColor(palette[index])

    def _normalize_image_bytes(self, value) -> bytes:
        if isinstance(value, memoryview):
            value = value.tobytes()
        if isinstance(value, bytearray):
            value = bytes(value)
        if isinstance(value, bytes):
            return value
        return b""

    def _ensure_image_application(self):
        global _IMAGE_APP
        app = QtWidgets.QApplication.instance()
        if app is not None:
            return app
        if _IMAGE_APP is None:
            _IMAGE_APP = QtWidgets.QApplication(["ogurec-image-generator"])
        return _IMAGE_APP

    def _get_or_create_customer(self, cursor: sqlite3.Cursor, full_name: str, place: str) -> int:
        row = cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE full_name = ? AND place = ?
            """,
            [full_name, place],
        ).fetchone()
        if row is not None:
            return row[0]

        cursor.execute(
            """
            INSERT INTO customers (full_name, place)
            VALUES (?, ?)
            """,
            [full_name, place],
        )
        return cursor.lastrowid

    def _delete_orphan_customer(self, cursor: sqlite3.Cursor, customer_id: int) -> None:
        remaining_orders = cursor.execute(
            "SELECT COUNT(*) FROM orders WHERE customer_id = ?",
            [customer_id],
        ).fetchone()[0]
        if remaining_orders == 0:
            cursor.execute("DELETE FROM customers WHERE customer_id = ?", [customer_id])

    def _require_connection(self) -> sqlite3.Connection:
        if not self.connection:
            raise RuntimeError("Соединение с базой данных не установлено.")
        return self.connection
