from database.db import get_db_connection, get_dict_cursor

def create_fee_payment(student_id: int, monthly_fee: int, yearly_fee: int, amount: int, payment_mod: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO fee_payment (student_id, monthly_fee, yearly_fee, amount, payment_mod) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (student_id, monthly_fee, yearly_fee, amount, payment_mod)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "student_id": student_id,
        "monthly_fee": monthly_fee,
        "yearly_fee": yearly_fee,
        "amount": amount,
        "payment_mod": payment_mod
    }

def get_fee_payments_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, student_id, monthly_fee, yearly_fee, amount, payment_date, payment_mod FROM fee_payment WHERE student_id = %s ORDER BY payment_date DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "student_id": row["student_id"],
            "monthly_fee": row["monthly_fee"],
            "yearly_fee": row["yearly_fee"],
            "amount": row["amount"],
            "payment_date": row["payment_date"],
            "payment_mod": row["payment_mod"]
        }
        for row in rows
    ]