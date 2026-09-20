from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from models.schemas import homeworkcreate
from services.homework_service import (
    create_homework,
    get_homework_by_student,
    get_homework_by_class,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/homework", tags=["Homework"])


class BulkHomeworkCreate(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: str
    deadline: str
    student_ids: Optional[List[int]] = None  # None = all students in class


@router.post("/", status_code=201)
def add_homework(
    hw_data: homeworkcreate,
    current_user: dict = Depends(get_current_user)
):
    result = create_homework(
        hw_data.student_id,
        hw_data.subject_id,
        hw_data.teacher_id,
        hw_data.title,
        hw_data.description,
        hw_data.deadline
    )
    return result


@router.post("/bulk", status_code=201)
def add_bulk_homework(
    data: BulkHomeworkCreate,
    current_user: dict = Depends(get_current_user)
):
    """Ek hi baar mein poori class ko homework assign karo."""
    from database.db import get_db_connection, get_dict_cursor

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    try:
        # Agar student_ids nahi diye — poori class ke students lo
        target_ids = data.student_ids
        if not target_ids:
            cursor.execute(
                "SELECT id FROM students WHERE class_id = %s AND deleted_at IS NULL",
                (data.class_id,)
            )
            target_ids = [r["id"] for r in cursor.fetchall()]

        if not target_ids:
            raise HTTPException(status_code=400, detail="Is class mein koi student nahi")

        # Ek hi transaction mein saare insert karo
        inserted = []
        for sid in target_ids:
            cursor.execute(
                """INSERT INTO homework 
                   (student_id, subject_id, teacher_id, title, description, deadline) 
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (sid, data.subject_id, data.teacher_id, data.title, data.description, data.deadline)
            )
            inserted.append(cursor.fetchone()["id"])

        conn.commit()

        return {
            "message": f"Homework assigned to {len(inserted)} students",
            "count": len(inserted),
            "ids": inserted,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Bulk homework error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/student/{student_id}")
def get_homework(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    return get_homework_by_student(student_id)


@router.get("/class/{class_id}")
def get_homework_class(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Class ki saari homework (poori class)."""
    return get_homework_by_class(class_id)