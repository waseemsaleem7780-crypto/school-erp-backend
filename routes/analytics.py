from fastapi import APIRouter, Depends
from database.db import get_db_connection, get_dict_cursor
from utils.dependencies import get_current_user, get_current_school_id

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ═══════════════════════════════════════════════════════════
# 1. ATTENDANCE TREND — Last 6 months
# ═══════════════════════════════════════════════════════════
@router.get("/attendance-trend")
def attendance_trend(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    conn = None
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT
                TO_CHAR(date, 'YYYY-MM') AS month,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present
            FROM attendance
            WHERE date >= NOW() - INTERVAL '6 months'
            GROUP BY TO_CHAR(date, 'YYYY-MM')
            ORDER BY month
        """)
        rows = cur.fetchall()
        cur.close()

        trend = []
        for r in rows:
            total = r['total'] or 0
            present = r['present'] or 0
            pct = round((present / total) * 100, 2) if total > 0 else 0
            trend.append({
                "month": r['month'],
                "percentage": pct,
                "present": present,
                "total": total,
            })
        return trend

    except Exception as e:
        print("Attendance trend error:", e)
        return []
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════════════════
# 2. FEE COLLECTION — Last 6 months
# ═══════════════════════════════════════════════════════════
@router.get("/fee-collection")
def fee_collection(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    conn = None
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT
                TO_CHAR(paid_date, 'YYYY-MM') AS month,
                SUM(amount) AS total
            FROM fee_payment
            WHERE paid_date >= NOW() - INTERVAL '6 months'
            GROUP BY TO_CHAR(paid_date, 'YYYY-MM')
            ORDER BY month
        """)
        rows = cur.fetchall()
        cur.close()

        result = []
        for r in rows:
            result.append({
                "month": r['month'],
                "total": float(r['total'] or 0),
            })
        return result

    except Exception as e:
        print("Fee collection error:", e)
        return []
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════════════════
# 3. TOP STUDENTS
# ═══════════════════════════════════════════════════════════
@router.get("/top-students")
def top_students(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    conn = None
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT
                s.id AS student_id,
                s.name AS student_name,
                s.roll_number,
                COUNT(a.id) AS total_days,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present_days
            FROM students s
            INNER JOIN attendance a ON a.student_id = s.id
            GROUP BY s.id, s.name, s.roll_number
            HAVING COUNT(a.id) > 0
            ORDER BY (SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)::float / COUNT(a.id)) DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
        cur.close()

        students = []
        for r in rows:
            total = r['total_days'] or 0
            present = r['present_days'] or 0
            pct = round((present / total) * 100, 2) if total > 0 else 0
            students.append({
                "student_id": r['student_id'],
                "student_name": r['student_name'],
                "roll_number": r['roll_number'],
                "present_days": present,
                "total_days": total,
                "percentage": pct,
            })
        return students

    except Exception as e:
        print("Top students error:", e)
        return []
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════════════════
# 4. FEE DEFAULTERS
# ═══════════════════════════════════════════════════════════
@router.get("/defaulters")
def fee_defaulters(
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id),
):
    conn = None
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)
        cur.execute("""
            SELECT DISTINCT
                s.id AS student_id,
                s.name AS student_name,
                s.roll_number
            FROM students s
            INNER JOIN fee_payment f ON f.student_id = s.id
            WHERE f.status = 'pending'
            ORDER BY s.roll_number
        """)
        rows = cur.fetchall()
        cur.close()

        return [
            {
                "student_id": r['student_id'],
                "student_name": r['student_name'],
                "roll_number": r['roll_number'],
            }
            for r in rows
        ]

    except Exception as e:
        print("Defaulters error:", e)
        return []
    finally:
        if conn:
            conn.close()