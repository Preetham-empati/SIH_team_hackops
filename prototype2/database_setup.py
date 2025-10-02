import sqlite3

def setup_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Create the users table (if not exists)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            is_verified BOOLEAN NOT NULL DEFAULT 0,
            gender TEXT,
            study_age INTEGER,
            interests TEXT,
            achievements TEXT,
            aspirations TEXT,
            profile_picture TEXT DEFAULT 'default_profile.png',
            profile_complete BOOLEAN NOT NULL DEFAULT 0
        )
    ''')

    # Create the pathways table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pathways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pathway_data TEXT NOT NULL, -- Storing the generated JSON data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    print("Database and tables created/updated successfully.")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()
