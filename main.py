from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db

from routes.auth import router as auth_router
from routes.classes import router as classes_router
from routes.sections import router as sections_router
from routes.subjects import router as subjects_router
from routes.students import router as students_router
from routes.teachers import router as teachers_router
from routes.attendance import router as attendance_router
from routes.guardians import router as guardians_router
from routes.timetable import router as timetable_router
from routes.fee_structure import router as fee_structure_router
from routes.fee_payment import router as fee_payment_router
from routes.concession import router as concession_router
from routes.homework import router as homework_router
from routes.exam import router as exam_router
from routes.results import router as results_router
from routes.assignment import router as assignment_router
from routes.notice_board import router as notice_board_router
from routes.study_material import router as study_material_router
from routes.academic_years import router as academic_years_router
from routes.school_settings import router as school_settings_router
from routes.dashboard import router as dashboard_router
from routes.teacher_dashboard import router as teacher_dashboard_router
from routes.student_dashboard import router as student_dashboard_router
from routes.upload import router as upload_router
from routes.teacher_dashboard import router as teacher_dashboard_router
from routes.analytics import router as analytics_router

app = FastAPI(title="School ERP System", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

init_db()

app.include_router(auth_router, prefix="/api")
app.include_router(classes_router, prefix="/api")
app.include_router(sections_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(teachers_router, prefix="/api")
app.include_router(attendance_router, prefix="/api")
app.include_router(guardians_router, prefix="/api")
app.include_router(timetable_router, prefix="/api")
app.include_router(fee_structure_router, prefix="/api")
app.include_router(fee_payment_router, prefix="/api")
app.include_router(concession_router, prefix="/api")
app.include_router(homework_router, prefix="/api")
app.include_router(exam_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(assignment_router, prefix="/api")
app.include_router(notice_board_router, prefix="/api")
app.include_router(study_material_router, prefix="/api")
app.include_router(academic_years_router, prefix="/api")
app.include_router(school_settings_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(teacher_dashboard_router, prefix="/api")
app.include_router(student_dashboard_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(teacher_dashboard_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

@app.get("/")
def home():
    return {"message": "School ERP System is Running!", "total_modules": 20}