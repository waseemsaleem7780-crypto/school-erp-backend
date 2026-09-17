from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from services.pdf_service import generate_student_report_card
from utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/pdf", tags=["PDF Reports"])


@router.get("/student/{student_id}/report-card")
def student_report_card(
    student_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin or teacher can access")

    pdf_buffer = generate_student_report_card(student_id)
    if not pdf_buffer:
        raise HTTPException(status_code=404, detail="Student not found")

    filename = f"report_card_{student_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )