
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "tasks.db"


class TasksApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Пример использования SQLite и Python")
        self.geometry("900x600")
        self.minsize(820, 520)

        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_table()

        self.task_id_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Not Started")
        self.search_var = tk.StringVar()

        self.build_ui()
        self.load_tasks()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'Not Started'
        )
        """)
        self.conn.commit()

    def build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        title_lbl = ttk.Label(
            main,
            text="Приложение для управления задачами (SQLite + Tkinter)",
            font=("Arial", 14, "bold")
        )
        title_lbl.pack(anchor="w", pady=(0, 10))

        form = ttk.LabelFrame(main, text="Поля ввода", padding=12)
        form.pack(fill="x")

        ttk.Label(form, text="ID:").grid(row=0, column=0, sticky="w", padx=5, pady=6)
        id_entry = ttk.Entry(form, textvariable=self.task_id_var, width=15, state="readonly")
        id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=6)

        ttk.Label(form, text="Название задачи:").grid(row=0, column=2, sticky="w", padx=5, pady=6)
        title_entry = ttk.Entry(form, textvariable=self.title_var, width=35)
        title_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=6)

        ttk.Label(form, text="Статус:").grid(row=0, column=4, sticky="w", padx=5, pady=6)
        status_box = ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=["Not Started", "In Progress", "Completed"],
            state="readonly",
            width=18
        )
        status_box.grid(row=0, column=5, sticky="w", padx=5, pady=6)

        form.columnconfigure(3, weight=1)

        buttons = ttk.Frame(main, padding=(0, 10, 0, 10))
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Добавить задачу", command=self.add_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="Изменить задачу", command=self.update_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="Удалить задачу", command=self.delete_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="Очистить поля", command=self.clear_fields).pack(side="left", padx=4)
        ttk.Button(buttons, text="Обновить список", command=self.load_tasks).pack(side="left", padx=4)

        search_frame = ttk.LabelFrame(main, text="Поиск", padding=10)
        search_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(search_frame, text="Название:").pack(side="left", padx=5)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_tasks).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Показать все", command=self.load_tasks).pack(side="left", padx=5)

        table_frame = ttk.LabelFrame(main, text="Список задач", padding=8)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Название задачи")
        self.tree.heading("status", text="Статус")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("title", width=460, anchor="w")
        self.tree.column("status", width=180, anchor="center")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def add_task(self):
        title = self.title_var.get().strip()
        status = self.status_var.get().strip()

        if not title:
            messagebox.showwarning("Предупреждение", "Введите название задачи.")
            return

        self.cursor.execute(
            "INSERT INTO Tasks (title, status) VALUES (?, ?)",
            (title, status)
        )
        self.conn.commit()
        self.load_tasks()
        self.clear_fields()
        messagebox.showinfo("Успех", "Задача добавлена.")

    def update_task(self):
        task_id = self.task_id_var.get().strip()
        title = self.title_var.get().strip()
        status = self.status_var.get().strip()

        if not task_id:
            messagebox.showwarning("Предупреждение", "Выберите задачу из таблицы.")
            return

        if not title:
            messagebox.showwarning("Предупреждение", "Введите название задачи.")
            return

        self.cursor.execute(
            "UPDATE Tasks SET title = ?, status = ? WHERE id = ?",
            (title, status, task_id)
        )
        self.conn.commit()
        self.load_tasks()
        self.clear_fields()
        messagebox.showinfo("Успех", "Задача изменена.")

    def delete_task(self):
        task_id = self.task_id_var.get().strip()

        if not task_id:
            messagebox.showwarning("Предупреждение", "Выберите задачу из таблицы.")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            return

        self.cursor.execute("DELETE FROM Tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()
        self.clear_fields()
        messagebox.showinfo("Успех", "Задача удалена.")

    def load_tasks(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("SELECT * FROM Tasks ORDER BY id")
        rows = self.cursor.fetchall()

        for row in rows:
            self.tree.insert("", "end", values=row)

    def search_tasks(self):
        keyword = self.search_var.get().strip()

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute(
            "SELECT * FROM Tasks WHERE title LIKE ? ORDER BY id",
            (f"%{keyword}%",)
        )
        rows = self.cursor.fetchall()

        for row in rows:
            self.tree.insert("", "end", values=row)

    def on_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        self.task_id_var.set(values[0])
        self.title_var.set(values[1])
        self.status_var.set(values[2])

    def clear_fields(self):
        self.task_id_var.set("")
        self.title_var.set("")
        self.status_var.set("Not Started")

    def on_close(self):
        self.conn.close()
        self.destroy()


if __name__ == "__main__":
    app = TasksApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()



пувупуе45н4
