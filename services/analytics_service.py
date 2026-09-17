from database.db import get_db_connection, get_dict_cursor


def get_attendance_trend():
    """Last 6 months ka attendance trend"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT 
                TO_CHAR(date, 'YYYY-MM') as month,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'present') as present
            FROM attendance 
            WHERE date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(date, 'YYYY-MM')
            ORDER BY month
        """)
        rows = cursor.fetchall()
        return [
            {
                "month": r["month"],
                "total": r["total"],
                "present": r["present"],
                "percentage": round((r["present"] / r["total"] * 100), 2) if r["total"] > 0 else 0
            }
            for r in rows
        ]
    except Exception as e:
        print("attendance trend error:", e)
        return []
    finally:
        conn.close()


def get_fee_collection():
    """Last 6 months ki fee collection"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT 
                TO_CHAR(payment_date, 'YYYY-MM') as month,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total
            FROM fee_payment 
            WHERE payment_date >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(payment_date, 'YYYY-MM')
            ORDER BY month
        """)
        rows = cursor.fetchall()
        return [
            {
                "month": r["month"],
                "count": r["count"],
                "total": float(r["total"]) if r["total"] else 0
            }
            for r in rows
        ]
    except Exception as e:
        print("fee collection error:", e)
        return []
    finally:
        conn.close()


def get_top_students(limit: int = 10):
    """Top students by attendance %"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT 
                s.id as student_id,
                s.roll_number,
                u.full_name as student_name,
                COUNT(a.id) as total_days,
                COUNT(a.id) FILTER (WHERE a.status = 'present') as present_days,
                ROUND(
                    COUNT(a.id) FILTER (WHERE a.status = 'present')::numeric / 
                    NULLIF(COUNT(a.id), 0) * 100, 
                    2
                ) as percentage
            FROM students s
            LEFT JOIN users u ON u.id = s.user_id
            LEFT JOIN attendance a ON a.student_id = s.id
            GROUP BY s.id, s.roll_number, u.full_name
            HAVING COUNT(a.id) > 0
            ORDER BY percentage DESC NULLS LAST
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        return [
            {
                "student_id": r["student_id"],
                "roll_number": r["roll_number"],
                "student_name": r["student_name"] or f"Student #{r['student_id']}",
                "total_days": r["total_days"],
                "present_days": r["present_days"],
                "percentage": float(r["percentage"]) if r["percentage"] else 0
            }
            for r in rows
        ]
    except Exception as e:
        print("top students error:", e)
        return []
    finally:
        conn.close()


def get_fee_defaulters():
    """Students with pending fees"""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT 
                s.id as student_id,
                s.roll_number,
                u.full_name as student_name,
                COUNT(fp.id) as payment_count
            FROM students s
            LEFT JOIN users u ON u.id = s.user_id
            LEFT JOIN fee_payment fp ON fp.student_id = s.id
            GROUP BY s.id, s.roll_number, u.full_name
            HAVING COUNT(fp.id) = 0
            ORDER BY s.roll_number
        """)
        rows = cursor.fetchall()
        return [
            {
                "student_id": r["student_id"],
                "roll_number": r["roll_number"],
                "student_name": r["student_name"] or f"Student #{r['student_id']}",
            }
            for r in rows
        ]
    except Exception as e:
        print("defaulters error:", e)
        return []
    finally:
        conn.close()