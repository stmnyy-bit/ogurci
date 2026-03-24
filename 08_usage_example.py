import sqlite3

connection = sqlite3.connect("tasks.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'Not Started'
)
""")

def add_task(title):
    cursor.execute("INSERT INTO Tasks (title) VALUES (?)", (title,))
    connection.commit()

def update_task_status(task_id, status):
    cursor.execute("UPDATE Tasks SET status = ? WHERE id = ?", (status, task_id))
    connection.commit()

def list_tasks():
    cursor.execute("SELECT * FROM Tasks")
    tasks = cursor.fetchall()
    for task in tasks:
        print(task)

add_task("Подготовить презентацию")
add_task("Закончить отчет")
add_task("Подготовить ужин")

update_task_status(2, "In Progress")

list_tasks()

connection.close()
