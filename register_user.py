import bcrypt
import sqlite3


def register_user(username, password):
    conn = sqlite3.connect("chat_users.db")
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect("chat_users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[0]):
        return True
    else:
        return False
