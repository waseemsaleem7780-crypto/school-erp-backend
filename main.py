from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db

# -------------------- AUTH --------------------
from routes.auth import router as auth_router

# -------------------- CORE --------------------
from routes.classes import router as classes_router
from routes.sections import router as sections_router
from routes.subjects import router as subjects_router
from routes.students import router as students_router

# -------------------- STAFF & ATTENDANCE --------------------
from routes.teachers import router as teachers_router
from routes.attendance import router as attendance_router
from routes.guardians import router as guardians_router

# -------------------- TIMETABLE --------------------
from routes.timetable import router as timetable_router

# -------------------- FEE --------------------
from routes.fee_structure import router as fee_structure_router
from routes.fee_payment import router as fee_payment_router
from routes.concession import router as concession_router

# -------------------- ACADEMICS --------------------
from routes.homework import router as homework_router
from routes.exam import router as exam_router
from routes.results import router as results_router
from routes.assignment import router as assignment_router

# -------------------- ADMIN / UTILITIES --------------------
from routes.notice_board import router as notice_board_router
from routes.study_material import router as study_material_router
from routes.academic_years import router as academic_years_router
from routes.school_settings import router as school_settings_router
from routes.dashboard import router as dashboard_router

# -------------------- APP SETUP --------------------
app = FastAPI(title="School ERP System", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://school-erp-frontend-azure.vercel.app",
        "https://school-erp-frontend-git-main-acme-1310.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

init_db()

# -------------------- REGISTER ALL ROUTERS --------------------
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

# -------------------- HOME ENDPOINT --------------------
@app.get("/")
def home():
    return {"message": "School ERP System is Running!", "total_modules": 20}