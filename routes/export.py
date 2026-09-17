from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from services.export_service import (
    export_students_excel,
    export_attendance_excel,
    export_fees_excel,
)
from utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/students/excel")
def export_students(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can export")

    output = export_students_excel()
    filename = f"students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/attendance/excel")
def export_attendance(
    class_id: int = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can export")

    output = export_attendance_excel(class_id)
    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/fees/excel")
def export_fees(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can export")

    output = export_fees_excel()
    filename = f"fees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )