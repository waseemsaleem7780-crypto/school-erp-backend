from database.db import get_db_connection, get_dict_cursor


def get_student_stats(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return {
            "attendance_present": 0,
            "attendance_total": 0,
            "homework_pending": 0,
            "results_count": 0,
            "fee_status": "N/A",
        }

    student_id = student["id"]

    # Attendance present count
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE student_id = %s AND status = 'present'",
        (student_id,)
    )
    present = cursor.fetchone()["count"]

    # Attendance total
    cursor.execute(
        "SELECT COUNT(*) as count FROM attendance WHERE student_id = %s",
        (student_id,)
    )
    total_attendance = cursor.fetchone()["count"]

    # Homework count
    cursor.execute(
        "SELECT COUNT(*) as count FROM homework WHERE student_id = %s",
        (student_id,)
    )
    homework_count = cursor.fetchone()["count"]

    # Results count
    cursor.execute(
        "SELECT COUNT(*) as count FROM results WHERE student_id = %s",
        (student_id,)
    )
    results_count = cursor.fetchone()["count"]

    # Fee status
    cursor.execute(
        "SELECT COUNT(*) as count FROM fee_payment WHERE student_id = %s",
        (student_id,)
    )
    fee_payments = cursor.fetchone()["count"]
    fee_status = "Paid ✅" if fee_payments > 0 else "Pending ⏰"

    conn.close()

    return {
        "attendance_present": present,
        "attendance_total": total_attendance,
        "homework_pending": homework_count,
        "results_count": results_count,
        "fee_status": fee_status,
    }


def get_student_attendance(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return []

    cursor.execute(
        "SELECT id, date, status FROM attendance WHERE student_id = %s ORDER BY date DESC",
        (student["id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "date": str(row["date"]),
            "status": row["status"],
        }
        for row in rows
    ]


def get_student_results(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return []

    cursor.execute(
        """SELECT id, exam_id, subject_id, marks_obtained, grade, remarks 
           FROM results WHERE student_id = %s""",
        (student["id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "exam_id": row["exam_id"],
            "subject_id": row["subject_id"],
            "marks_obtained": float(row["marks_obtained"]) if row["marks_obtained"] else 0,
            "grade": row.get("grade", "N/A"),
            "remarks": row.get("remarks", ""),
        }
        for row in rows
    ]


def get_student_fees(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return []

    # Sirf confirmed columns use karo (payment_mod nahi hai)
    cursor.execute(
        """SELECT id, amount, monthly_fee, yearly_fee 
           FROM fee_payment WHERE student_id = %s""",
        (student["id"],)
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "amount": row["amount"],
            "monthly_fee": row.get("monthly_fee", 0),
            "yearly_fee": row.get("yearly_fee", 0),
        }
        for row in rows
    ]