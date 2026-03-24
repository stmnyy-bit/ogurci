import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

print("Пользователи старше 25:")
cursor.execute("SELECT username, age FROM Users WHERE age > ?", (25,))
for row in cursor.fetchall():
    print(row)

print("\nСредний возраст по возрастам:")
cursor.execute("SELECT age, AVG(age) FROM Users GROUP BY age")
for row in cursor.fetchall():
    print(row)

print("\nГруппы со средним возрастом больше 30:")
cursor.execute("SELECT age, AVG(age) FROM Users GROUP BY age HAVING AVG(age) > ?", (30,))
for row in cursor.fetchall():
    print(row)

print("\nСортировка по возрасту по убыванию:")
cursor.execute("SELECT username, age FROM Users ORDER BY age DESC")
for row in cursor.fetchall():
    print(row)

connection.close()
