import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

cursor.execute(
    "INSERT INTO Users (username, email, age) VALUES (?, ?, ?)",
    ("newuser", "newuser@example.com", 28)
)

cursor.execute(
    "UPDATE Users SET age = ? WHERE username = ?",
    (29, "newuser")
)

cursor.execute(
    "DELETE FROM Users WHERE username = ?",
    ("newuser",)
)

connection.commit()
connection.close()

print("Операции INSERT, UPDATE, DELETE выполнены.")
