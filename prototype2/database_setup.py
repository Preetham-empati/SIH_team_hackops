# (in database_setup.py)
import sqlite3

def setup_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Create the users table with all required columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            is_verified BOOLEAN NOT NULL DEFAULT 0
        )
    ''')

    print("Database and table created successfully with all columns.")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()