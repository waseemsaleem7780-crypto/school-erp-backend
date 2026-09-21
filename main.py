from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from database.db import init_db
import os

# ✅ Security (Phase 1)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routes.auth import router as auth_router
from routes.schools import router as schools_router
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
from routes.analytics import router as analytics_router
from routes.export import router as export_router
from routes.pdf import router as pdf_router
from routes.backup import router as backup_router
from routes import attendance
from routes import chatbot
from routes import audit
from routes import broadcast
from routes import teacher_message
from routes import whatsapp
from routes import notification

app = FastAPI(title="School ERP System", version="1.0")

# ✅ Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═══════════════════════════════════════════════════════════════
#  ✅ CORS — HTTP-Only Cookies support ke liye
# ═══════════════════════════════════════════════════════════════
# ⚠️ IMPORTANT: allow_origins=["*"] ke saath credentials KAAM NAHI karta
# Explicit origins list karo

ALLOWED_ORIGINS = [
    "https://school-erp-frontend-azure.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

# Env var se additional origins add karo (comma-separated)
extra_origins = os.getenv("CORS_ORIGINS")
if extra_origins:
    ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,      # ✅ Cookies allow karo
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ✅ Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

init_db()

# ============ ROUTERS ============
app.include_router(auth_router, prefix="/api")
app.include_router(schools_router, prefix="/api")
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
app.include_router(analytics_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(pdf_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(broadcast.router, prefix="/api")
app.include_router(teacher_message.router, prefix="/api")
app.include_router(whatsapp.router, prefix="/api")
app.include_router(notification.router, prefix="/api")


@app.get("/")
def home():
    return {"message": "School ERP System is Running!", "total_modules": 20}