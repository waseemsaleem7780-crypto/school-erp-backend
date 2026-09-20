from fastapi import APIRouter, Depends, HTTPException
from models.schemas import resultcreate
from services.results_service import create_result, get_results_by_student
from services.notification_service import notify_result
from utils.dependencies import get_current_user, get_current_school_id
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/results", tags=["Results"])


@router.post("/", status_code=201)
def add_result(
    result_data: resultcreate,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """Result add karo + parent ko WhatsApp bhejo."""
    result = create_result(
        result_data.exam_id,
        result_data.student_id,
        result_data.subject_id,
        result_data.marks_obtained,
        result_data.grade,
        result_data.remarks
    )

    try:
        conn = get_db_connection()
        cursor = get_dict_cursor(conn)
        cursor.execute(
            """SELECT e.name as exam_name, e.total_marks,
                      sub.name as subject_name
               FROM exam e
               LEFT JOIN subjects sub ON sub.id = %s
               WHERE e.id = %s""",
            (result_data.subject_id, result_data.exam_id)
        )
        info = cursor.fetchone()
        conn.close()

        if info:
            notify_result(
                school_id=school_id,
                student_id=result_data.student_id,
                exam_name=info["exam_name"] or "Exam",
                subject_name=info["subject_name"] or "Subject",
                marks=result_data.marks_obtained,
                total=info["total_marks"] or 100,
                grade=result_data.grade
            )
    except Exception as e:
        print(f"WhatsApp notification failed: {e}")

    return result


@router.get("/student/{student_id}")
def get_results(
    student_id: int,
    current_user: dict = Depends(get_current_user),
    school_id: int = Depends(get_current_school_id)
):
    """
    Ek student ke saare results.
    Frontend /auth/me se student_id le kar bhejta hai — safe hai.
    """
    return get_results_by_student(student_id)