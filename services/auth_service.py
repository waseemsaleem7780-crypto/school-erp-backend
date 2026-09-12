from database.db import get_db_connection, get_dict_cursor
from passlib.context import CryptContext
from models.schemas import usercreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str):
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, full_name, email, password, role FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_new_user(user_data: usercreate):
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        return {"error": "Email already exists"}

    hashed_password = hash_password(user_data.password)

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute(
        "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_data.full_name, user_data.email, hashed_password, user_data.role)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()

    return {
        "id": new_id,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "role": user_data.role
    }