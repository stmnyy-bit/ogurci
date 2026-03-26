import sqlite3
from pathlib import Path
from typing import Iterable, Optional


ALL_MANUFACTURERS = "Все производители"
ALL_PLACES = "Все города"
HIDDEN_VIEWS = {"clients"}


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
                discount_percent
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
                order_number,
                customer_id,
                tv_code,
                order_date,
                quantity,
                discount_percent
            FROM orders
            WHERE 1 = 1
        """
        params: list = []
        if search:
            pattern = f"%{search.strip()}%"
            sql += """
                AND (
                    CAST(order_number AS TEXT) LIKE ?
                    OR CAST(customer_id AS TEXT) LIKE ?
                    OR CAST(tv_code AS TEXT) LIKE ?
                    OR order_date LIKE ?
                )
            """
            params.extend([pattern, pattern, pattern, pattern])

        sort_sql = {
            "date_desc": " ORDER BY order_date DESC, order_number DESC",
            "date_asc": " ORDER BY order_date ASC, order_number ASC",
            "order_asc": " ORDER BY order_number ASC",
            "quantity_desc": " ORDER BY quantity DESC, order_number DESC",
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
        self.execute(
            """
            INSERT INTO televisions (
                tv_code, model_name, manufacturer, diagonal_cm, price, discount_percent
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                data["tv_code"],
                data["model_name"],
                data["manufacturer"],
                data["diagonal_cm"],
                data["price"],
                data["discount_percent"],
            ],
        )

    def update_television(self, tv_code: int, data: dict) -> None:
        self.execute(
            """
            UPDATE televisions
            SET model_name = ?, manufacturer = ?, diagonal_cm = ?, price = ?, discount_percent = ?
            WHERE tv_code = ?
            """,
            [
                data["model_name"],
                data["manufacturer"],
                data["diagonal_cm"],
                data["price"],
                data["discount_percent"],
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
