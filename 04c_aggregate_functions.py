import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM Users")
print("Количество пользователей:", cursor.fetchone()[0])

cursor.execute("SELECT SUM(age) FROM Users")
print("Сумма возрастов:", cursor.fetchone()[0])

cursor.execute("SELECT AVG(age) FROM Users")
print("Средний возраст:", cursor.fetchone()[0])

cursor.execute("SELECT MIN(age) FROM Users")
print("Минимальный возраст:", cursor.fetchone()[0])

cursor.execute("SELECT MAX(age) FROM Users")
print("Максимальный возраст:", cursor.fetchone()[0])

connection.close()
