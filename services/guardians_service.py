from database.db import get_db_connection, get_dict_cursor

def create_guardian(user_id: int, student_id: int, full_name: str, relation: str, phone_number: str, email: str, address: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO guardians (user_id, student_id, full_name, relation, phone_number, email, address) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (user_id, student_id, full_name, relation, phone_number, email, address)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "user_id": user_id,
        "student_id": student_id,
        "full_name": full_name,
        "relation": relation,
        "phone_number": phone_number,
        "email": email,
        "address": address
    }

def get_guardians_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, user_id, student_id, full_name, relation, phone_number, email, address FROM guardians WHERE student_id = %s ORDER BY id",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "student_id": row["student_id"],
            "full_name": row["full_name"],
            "relation": row["relation"],
            "phone_number": row["phone_number"],
            "email": row["email"],
            "address": row["address"]
        }
        for row in rows
    ]