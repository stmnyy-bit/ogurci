import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON Users (email)")

connection.commit()
connection.close()

print("Индекс по email создан.")
