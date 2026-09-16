from fastapi import APIRouter, Depends, HTTPException
from services.student_dashboard_service import (
    get_student_stats,
    get_student_attendance,
    get_student_results,
    get_student_fees,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/student/dashboard", tags=["Student Dashboard"])


def get_user_id(current_user: dict) -> int:
    return current_user.get("id") or current_user.get("user_id")


@router.get("/stats")
def student_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_stats(get_user_id(current_user))


@router.get("/attendance")
def student_attendance(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_attendance(get_user_id(current_user))


@router.get("/results")
def student_results(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_results(get_user_id(current_user))


@router.get("/fees")
def student_fees(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")
    return get_student_fees(get_user_id(current_user))


@router.post("/auto-create")
def auto_create_student_record(current_user: dict = Depends(get_current_user)):
    """Student user ke liye students table mein record auto-create karo."""
    from database.db import get_db_connection, get_dict_cursor

    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can access")

    user_id = get_user_id(current_user)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    # Check karo already record hai ya nahi
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return {"message": "Student record already exists", "student_id": existing["id"]}

    # Class 1 aur Section 1 use karo (ya jo exist kare)
    try:
        cursor.execute("SELECT id FROM classes LIMIT 1")
        cls = cursor.fetchone()
        class_id = cls["id"] if cls else 1
    except:
        class_id = 1

    try:
        cursor.execute("SELECT id FROM sections WHERE class_id = %s LIMIT 1", (class_id,))
        sec = cursor.fetchone()
        section_id = sec["id"] if sec else 1
    except:
        section_id = 1

    # Insert student
    cursor.execute(
        """INSERT INTO students (user_id, roll_number, class_id, section_id) 
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (user_id, f"AUTO-{user_id}", class_id, section_id)
    )
    student_id = cursor.fetchone()["id"]
    conn.commit()

    # Test attendance add karo (10 days)
    from datetime import date, timedelta
    today = date.today()
    for i in range(10):
        d = today - timedelta(days=i)
        status = 'half_day' if i == 3 else 'present'
        cursor.execute(
            """INSERT INTO attendance (student_id, date, status, marked_by) 
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (student_id, date) DO NOTHING""",
            (student_id, d, status, 1)
        )
    conn.commit()
    conn.close()

    return {
        "message": "Student record created with test data",
        "student_id": student_id,
        "attendance_added": 10,
    }