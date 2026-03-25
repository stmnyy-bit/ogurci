
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = "my_database.db"


class TasksApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Пример SQLite (my_database.db)")
        self.geometry("900x600")

        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_table()

        self.task_id_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Not Started")

        self.build_ui()
        self.load_tasks()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT
        )
        """)
        self.conn.commit()

    def build_ui(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        form = ttk.LabelFrame(frame, text="Поля ввода", padding=10)
        form.pack(fill="x")

        ttk.Label(form, text="ID").grid(row=0, column=0)
        ttk.Entry(form, textvariable=self.task_id_var, state="readonly").grid(row=0, column=1)

        ttk.Label(form, text="Название").grid(row=0, column=2)
        ttk.Entry(form, textvariable=self.title_var, width=30).grid(row=0, column=3)

        ttk.Label(form, text="Статус").grid(row=0, column=4)
        ttk.Combobox(form, textvariable=self.status_var,
                     values=["Not Started", "In Progress", "Completed"],
                     state="readonly").grid(row=0, column=5)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=10)

        ttk.Button(btns, text="Добавить", command=self.add_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Изменить", command=self.update_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Удалить", command=self.delete_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Обновить", command=self.load_tasks).pack(side="left", padx=5)

        self.tree = ttk.Treeview(frame, columns=("id", "title", "status"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Название")
        self.tree.heading("status", text="Статус")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.select_task)

    def add_task(self):
        self.cursor.execute("INSERT INTO Tasks (title, status) VALUES (?, ?)",
                            (self.title_var.get(), self.status_var.get()))
        self.conn.commit()
        self.load_tasks()

    def update_task(self):
        self.cursor.execute("UPDATE Tasks SET title=?, status=? WHERE id=?",
                            (self.title_var.get(), self.status_var.get(), self.task_id_var.get()))
        self.conn.commit()
        self.load_tasks()

    def delete_task(self):
        self.cursor.execute("DELETE FROM Tasks WHERE id=?",
                            (self.task_id_var.get(),))
        self.conn.commit()
        self.load_tasks()

    def load_tasks(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.cursor.execute("SELECT * FROM Tasks"):
            self.tree.insert("", "end", values=row)

    def select_task(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.task_id_var.set(values[0])
            self.title_var.set(values[1])
            self.status_var.set(values[2])


if __name__ == "__main__":
    app = TasksApp()
    app.mainloop()
