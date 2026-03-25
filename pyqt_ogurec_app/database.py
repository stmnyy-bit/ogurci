import sqlite3
from pathlib import Path
from typing import Iterable, Optional


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
        if isinstance(row, sqlite3.Row):
            return row[0]
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
        return [name for name, kind in self.object_names() if kind == "view"]

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
            FROM clients
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
        if manufacturer and manufacturer != "Все производители":
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

    def get_clients(
        self,
        search: str = "",
        place: str = "",
        sort_mode: str = "date_desc",
    ) -> list[dict]:
        sql = """
            SELECT
                c.order_number,
                c.tv_code,
                c.full_name,
                c.order_date,
                c.quantity,
                c.place,
                c.discount_percent,
                t.model_name
            FROM clients c
            LEFT JOIN televisions t ON t.tv_code = c.tv_code
            WHERE 1 = 1
        """
        params: list = []
        if search:
            pattern = f"%{search.strip()}%"
            sql += """
                AND (
                    CAST(c.order_number AS TEXT) LIKE ?
                    OR c.full_name LIKE ?
                    OR c.place LIKE ?
                    OR IFNULL(t.model_name, '') LIKE ?
                )
            """
            params.extend([pattern, pattern, pattern, pattern])
        if place and place != "Все города":
            sql += " AND c.place = ?"
            params.append(place)

        sort_sql = {
            "date_desc": " ORDER BY c.order_date DESC, c.order_number DESC",
            "date_asc": " ORDER BY c.order_date ASC, c.order_number ASC",
            "name_asc": " ORDER BY c.full_name ASC",
            "quantity_desc": " ORDER BY c.quantity DESC, c.order_number DESC",
        }
        sql += sort_sql.get(sort_mode, sort_sql["date_desc"])
        return [dict(row) for row in self.query(sql, params)]

    def get_view_rows(self, view_name: str) -> tuple[list[str], list[dict]]:
        if view_name not in self.list_views():
            raise ValueError(f"Представление {view_name} не найдено в базе.")
        rows = self.query(f'SELECT * FROM "{view_name}"')
        if not rows:
            columns = self.get_columns(view_name)
            return columns, []
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

    def get_client(self, order_number: int) -> Optional[dict]:
        rows = self.query("SELECT * FROM clients WHERE order_number = ?", [order_number])
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

    def add_client(self, data: dict) -> None:
        self.execute(
            """
            INSERT INTO clients (
                order_number, tv_code, full_name, order_date, quantity, place, discount_percent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                data["order_number"],
                data["tv_code"],
                data["full_name"],
                data["order_date"],
                data["quantity"],
                data["place"],
                data["discount_percent"],
            ],
        )

    def update_client(self, order_number: int, data: dict) -> None:
        self.execute(
            """
            UPDATE clients
            SET tv_code = ?, full_name = ?, order_date = ?, quantity = ?, place = ?, discount_percent = ?
            WHERE order_number = ?
            """,
            [
                data["tv_code"],
                data["full_name"],
                data["order_date"],
                data["quantity"],
                data["place"],
                data["discount_percent"],
                order_number,
            ],
        )

    def delete_client(self, order_number: int) -> None:
        self.execute("DELETE FROM clients WHERE order_number = ?", [order_number])

    def dashboard_stats(self) -> dict:
        television_count = self.scalar("SELECT COUNT(*) FROM televisions") or 0
        order_count = self.scalar("SELECT COUNT(*) FROM clients") or 0
        view_count = self.scalar(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'view' AND name NOT LIKE 'sqlite_%'
            """
        ) or 0
        average_price = self.scalar("SELECT ROUND(AVG(price), 2) FROM televisions") or 0
        total_revenue = self.scalar(
            """
            SELECT ROUND(SUM(c.quantity * t.price * (100 - c.discount_percent) / 100.0), 2)
            FROM clients c
            JOIN televisions t ON t.tv_code = c.tv_code
            """
        ) or 0
        top_manufacturer = self.scalar(
            """
            SELECT manufacturer
            FROM televisions
            GROUP BY manufacturer
            ORDER BY COUNT(*) DESC, manufacturer
            LIMIT 1
            """
        ) or "-"
        return {
            "television_count": television_count,
            "order_count": order_count,
            "view_count": view_count,
            "average_price": average_price,
            "total_revenue": total_revenue,
            "top_manufacturer": top_manufacturer,
        }

    def _require_connection(self) -> sqlite3.Connection:
        if not self.connection:
            raise RuntimeError("Соединение с базой не установлено.")
        return self.connection
