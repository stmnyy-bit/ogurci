import sqlite3

connection = sqlite3.connect("my_database.db")
print("База данных подключена или создана успешно.")

connection.close()
print("Соединение закрыто.")
