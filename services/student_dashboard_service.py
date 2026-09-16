from database.db import get_db_connection, get_dict_cursor


def get_student_stats(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    result = {
        "attendance_present": 0,
        "attendance_total": 0,
        "homework_pending": 0,
        "results_count": 0,
        "fee_status": "N/A",
    }
    try:
        cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return result
        student_id = student["id"]

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM attendance WHERE student_id = %s AND LOWER(status) = 'present'",
                (student_id,)
            )
            result["attendance_present"] = cursor.fetchone()["c"]
        except Exception as e:
            print("present error:", e)

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM attendance WHERE student_id = %s",
                (student_id,)
            )
            result["attendance_total"] = cursor.fetchone()["c"]
        except Exception as e:
            print("total error:", e)

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM homework WHERE student_id = %s",
                (student_id,)
            )
            result["homework_pending"] = cursor.fetchone()["c"]
        except Exception as e:
            print("homework error:", e)

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM results WHERE student_id = %s",
                (student_id,)
            )
            result["results_count"] = cursor.fetchone()["c"]
        except Exception as e:
            print("results error:", e)

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM fee_payment WHERE student_id = %s",
                (student_id,)
            )
            count = cursor.fetchone()["c"]
            result["fee_status"] = "Paid ✅" if count > 0 else "Pending ⏰"
        except Exception as e:
            print("fee error:", e)

        return result
    except Exception as e:
        print("stats error:", e)
        return result
    finally:
        conn.close()


def get_student_attendance(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return []
        cursor.execute(
            "SELECT id, date, status FROM attendance WHERE student_id = %s ORDER BY date DESC LIMIT 100",
            (student["id"],)
        )
        rows = cursor.fetchall()
        return [{"id": r["id"], "date": str(r["date"]), "status": r["status"]} for r in rows]
    except Exception as e:
        print("attendance error:", e)
        return []
    finally:
        conn.close()


def get_student_results(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return []
        cursor.execute(
            "SELECT * FROM results WHERE student_id = %s",
            (student["id"],)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r.get("id"),
                "exam_id": r.get("exam_id"),
                "subject_id": r.get("subject_id"),
                "marks_obtained": float(r["marks_obtained"]) if r.get("marks_obtained") else 0,
                "grade": r.get("grade") or "N/A",
                "remarks": r.get("remarks") or "",
            }
            for r in rows
        ]
    except Exception as e:
        print("results error:", e)
        return []
    finally:
        conn.close()


def get_student_fees(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return []
        cursor.execute(
            "SELECT * FROM fee_payment WHERE student_id = %s",
            (student["id"],)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r.get("id"),
                "amount": r.get("amount", 0),
                "monthly_fee": r.get("monthly_fee", 0),
                "yearly_fee": r.get("yearly_fee", 0),
            }
            for r in rows
        ]
    except Exception as e:
        print("fees error:", e)
        return []
    finally:
        conn.close()