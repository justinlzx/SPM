def create_user(db, uuid: str, email: str, username: str, hashed_password: str, role: str):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (UUID, email, username, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        (uuid, email, username, hashed_password, role)
    )
    db.commit()

def get_user_by_username(db, username: str):
    cursor = db.cursor()
    cursor.execute("SELECT UUID, email, username, hashed_password, role FROM users WHERE username = ?", (username,))
    return cursor.fetchone()

def get_user_by_email(db, email: str):
    cursor = db.cursor()
    cursor.execute("SELECT UUID, email, username, hashed_password, role FROM users WHERE email = ?", (email,))
    return cursor.fetchone()
