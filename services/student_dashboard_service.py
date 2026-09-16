from database.db import get_db_connection, get_dict_cursor


def get_student_stats(user_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
        student = cursor.fetchone()
        if not student:
            return {
                "attendance_present": 0,
                "attendance_total": 0,
                "homework_pending": 0,
                "results_count": 0,
                "fee_status": "N/A",
            }
        student_id = student["id"]

        # Attendance
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM attendance WHERE student_id = %s AND LOWER(status) = 'present'",
                (student_id,)
            )
            present = cursor.fetchone()["c"]
        except Exception as e:
            print("attendance present error:", e)
            present = 0

        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM attendance WHERE student_id = %s",
                (student_id,)
            )
            total_attendance = cursor.fetchone()["c"]
        except Exception as e:
            print("attendance total error:", e)
            total_attendance = 0

        # Homework
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM homework WHERE student_id = %s",
                (student_id,)
            )
            homework_count = cursor.fetchone()["c"]
        except Exception as e:
            print("homework error:", e)
            homework_count = 0

        # Results
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM results WHERE student_id = %s",
                (student_id,)
            )
            results_count = cursor.fetchone()["c"]
        except Exception as e:
            print("results error:", e)
            results_count = 0

        # Fee
        try:
            cursor.execute(
                "SELECT COUNT(*) as c FROM fee_payment WHERE student_id = %s",
                (student_id,)
            )
            fee_payments = cursor.fetchone()["c"]
        except Exception as e:
            print("fee error:", e)
            fee_payments = 0

        fee_status = "Paid ✅" if fee_payments > 0 else "Pending ⏰"

        return {
            "attendance_present": present,
            "attendance_total": total_attendance,
            "homework_pending": homework_count,
            "results_count": results_count,
            "fee_status": fee_status,
        }
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
        print("get_student_attendance error:", e)
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
            "SELECT id, exam_id, subject_id, marks_obtained, grade, remarks FROM results WHERE student_id = %s",
            (student["id"],)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "exam_id": r["exam_id"],
                "subject_id": r["subject_id"],
                "marks_obtained": float(r["marks_obtained"]) if r["marks_obtained"] else 0,
                "grade": r["grade"],
                "remarks": r["remarks"],
            }
            for r in rows
        ]
    except Exception as e:
        print("get_student_results error:", e)
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
            "SELECT id, amount, payment_mod, payment_date FROM fee_payment WHERE student_id = %s ORDER BY payment_date DESC",
            (student["id"],)
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "amount": r["amount"],
                "payment_mod": r["payment_mod"],
                "payment_date": str(r["payment_date"]),
            }
            for r in rows
        ]
    except Exception as e:
        print("get_student_fees error:", e)
        return []
    finally:
        conn.close()