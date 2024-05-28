from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

class User:
    @staticmethod
    def find_by_username(username):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def create_user(username, password):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, generate_password_hash(password)))
        conn.commit()
        conn.close()

    @staticmethod
    def validate_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)
