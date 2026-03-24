import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM Users")
first_user = cursor.fetchone()
print("fetchone():", first_user)

cursor.execute("SELECT * FROM Users")
first_five_users = cursor.fetchmany(5)
print("fetchmany(5):", first_five_users)

cursor.execute("SELECT * FROM Users")
all_users = cursor.fetchall()
print("fetchall():", all_users)

connection.close()
