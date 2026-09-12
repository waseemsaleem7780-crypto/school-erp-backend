from database.db import get_db_connection

def create_fee_structure(class_id: int, month: int, yearly_fee: int, amount: float, due_date: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO fee_structure (class_id, month, yearly_fee, amount, due_date) VALUES (?, ?, ?, ?, ?)",
        (class_id, month, yearly_fee, amount, due_date)
    )
    conn.commit()
    new_id = cursor.lastrowid
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
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, class_id, month, yearly_fee, amount, due_date FROM fee_structure WHERE class_id = ? ORDER BY month",
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