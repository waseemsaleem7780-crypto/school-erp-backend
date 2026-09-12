from database.db import get_db_connection, get_dict_cursor

def create_fee_structure(class_id: int, month: int, yearly_fee: int, amount: float, due_date: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO fee_structure (class_id, month, yearly_fee, amount, due_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (class_id, month, yearly_fee, amount, due_date)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "class_id": class_id,
        "month": month,
        "yearly_fee": yearly_fee,
        "amount": amount,
        "due_date": due_date
    }

def get_fee_structure_by_class(class_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, class_id, month, yearly_fee, amount, due_date FROM fee_structure WHERE class_id = %s ORDER BY month",
        (class_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "class_id": row["class_id"],
            "month": row["month"],
            "yearly_fee": row["yearly_fee"],
            "amount": row["amount"],
            "due_date": row["due_date"]
        }
        for row in rows
    ]