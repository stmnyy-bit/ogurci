import sqlite3

connection = sqlite3.connect("my_database.db")
cursor = connection.cursor()

query = "SELECT * FROM Users WHERE age > ?"
cursor.execute(query, (25,))
users = cursor.fetchall()
print("Пользователи старше 25:", users)

cursor.execute("""
CREATE VIEW IF NOT EXISTS ActiveUsers AS
SELECT * FROM Users
WHERE age IS NOT NULL
""")

cursor.execute("SELECT * FROM ActiveUsers")
print("ActiveUsers:", cursor.fetchall())

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users_Audit (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    action TEXT
)
""")

cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_after_insert_user
AFTER INSERT ON Users
BEGIN
    INSERT INTO Users_Audit (user_id, action)
    VALUES (NEW.id, 'INSERT');
END;
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON Users (username)")

connection.commit()
connection.close()

print("Продвинутые концепции выполнены.")
