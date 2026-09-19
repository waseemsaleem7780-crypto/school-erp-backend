from pydantic import BaseModel, EmailStr, validator
from datetime import date
from typing import Optional


# ============ AUTH ============
class userlogin(BaseModel):
    email: str
    password: str


class usercreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str
    school_id: Optional[int] = None
    phone: Optional[str] = None

    @validator('role')
    def validate_role(cls, v):
        v = v.lower()
        if v not in (['super_admin', 'admin', 'teacher', 'student', 'parent']):
            raise ValueError('Role must be one of: super_admin, admin, teacher, student, parent')
        return v


class userresponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    school_id: Optional[int] = None
    phone: Optional[str] = None
    created_at: date

    class Config:
        from_attributes = True


# ============ SCHOOLS ============
class schoolscreate(BaseModel):
    name: str
    subdomain: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: Optional[str] = "trial"
    subscription_expires_at: Optional[date] = None
    # ✅ WhatsApp fields (optional — Twilio ke liye)
    whatsapp_number: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None


class schoolscreate(BaseModel):
    name: str
    subdomain: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: Optional[str] = "trial"
    subscription_expires_at: Optional[date] = None
    # ✅ WhatsApp Config
    whatsapp_provider: Optional[str] = None      # 'twilio' / 'wab2c' / 'meta'
    whatsapp_number: Optional[str] = None
    whatsapp_account_sid: Optional[str] = None   # Twilio
    whatsapp_auth_token: Optional[str] = None    # Twilio
    whatsapp_api_key: Optional[str] = None       # WAB2C / Meta
    whatsapp_phone_id: Optional[str] = None      # Meta


# ============ CLASSES ============
class classescreate(BaseModel):
    name: str


class classesresponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ============ SECTIONS ============
class sectionscreate(BaseModel):
    name: str
    class_id: int


class sectionsresponse(BaseModel):
    id: int
    name: str
    class_id: int

    class Config:
        from_attributes = True


# ============ SUBJECTS ============
class subjectscreate(BaseModel):
    name: str
    code: str
    class_id: int
    teacher_id: Optional[int] = None


class subjectsresponse(BaseModel):
    id: int
    name: str
    code: str
    class_id: int
    teacher_id: Optional[int] = None

    class Config:
        from_attributes = True


# ============ TEACHERS ============
class teacherscreate(BaseModel):
    user_id: int
    qualification: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class teachersresponse(BaseModel):
    id: int
    user_id: int
    qualification: str
    phone: Optional[str] = None
    hired_date: date

    class Config:
        from_attributes = True


# ============ FEE STRUCTURE ============
class fee_structurecreate(BaseModel):
    class_id: int
    month: int
    yearly_fee: int
    amount: int
    due_date: date


class fee_structureresponse(BaseModel):
    id: int
    class_id: int
    month: int
    yearly_fee: int
    amount: int
    due_date: date

    class Config:
        from_attributes = True


# ============ FEE PAYMENT ============
class fee_paymentcreate(BaseModel):
    student_id: int
    monthly_fee: int
    yearly_fee: int
    amount: int
    payment_mod: str


class fee_paymentresponse(BaseModel):
    id: int
    student_id: int
    monthly_fee: int
    yearly_fee: int
    amount: int
    payment_date: date
    payment_mod: str

    class Config:
        from_attributes = True


# ============ HOMEWORK ============
class homeworkcreate(BaseModel):
    student_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: str
    deadline: date


class homeworkresponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: str
    deadline: date
    created_at: date

    class Config:
        from_attributes = True


# ============ EXAM ============
class examcreate(BaseModel):
    name: str
    class_id: int
    subject_id: int
    exam_date: date
    total_marks: int
    passing_marks: int


class examresponse(BaseModel):
    id: int
    name: str
    class_id: int
    subject_id: int
    exam_date: date
    total_marks: int
    passing_marks: int

    class Config:
        from_attributes = True


# ============ RESULTS ============
class resultcreate(BaseModel):
    exam_id: int
    student_id: int
    subject_id: int
    marks_obtained: int
    grade: str
    remarks: str


class resultresponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    subject_id: int
    marks_obtained: int
    grade: str
    remarks: str

    class Config:
        from_attributes = True


# ============ STUDENTS ============
class students(BaseModel):
    user_id: int
    class_id: int
    section_id: int
    roll_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    parent_whatsapp: Optional[str] = None   # ✅ Parent WhatsApp
    parent_name: Optional[str] = None       # ✅ Parent Name


class studentsresponse(BaseModel):
    id: int
    user_id: int
    class_id: int
    section_id: int
    roll_number: str
    parent_whatsapp: Optional[str] = None
    parent_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============ ATTENDANCE ============
class attendancecreate(BaseModel):
    student_id: int
    date: date
    status: str
    marked_by: int

    @validator('status')
    def validate_status(cls, v):
        v = v.lower()
        if v not in (['present', 'absent', 'half_day', 'leave']):
            raise ValueError("Invalid status value")
        return v


class attendanceresponse(BaseModel):
    id: int
    student_id: int
    date: date
    status: str
    marked_by: int
    marked_at: date

    class Config:
        from_attributes = True


# ============ GUARDIANS ============
class guardianscreate(BaseModel):
    user_id: int
    student_id: int
    full_name: str
    relation: str
    phone_number: str
    email: EmailStr
    address: str

    @validator('relation')
    def validate_relation(cls, v):
        v = v.lower()
        if v not in (['father', 'mother', 'guardian']):
            raise ValueError("Invalid relation value")
        return v


class guardiansresponse(BaseModel):
    id: int
    user_id: int
    student_id: int
    full_name: str
    relation: str
    phone_number: str
    email: EmailStr
    address: str

    class Config:
        from_attributes = True


# ============ TIMETABLE ============
class timetablecreate(BaseModel):
    class_id: int
    section_id: int
    subject_id: int
    teacher_id: int
    day_of_week: str
    start_time: str
    end_time: str

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        v = v.lower()
        if v not in (['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']):
            raise ValueError("Invalid day of week value")
        return v


class timetableresponse(BaseModel):
    id: int
    class_id: int
    section_id: int
    subject_id: int
    teacher_id: int
    day_of_week: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True


# ============ NOTICE BOARD ============
class notice_boardcreate(BaseModel):
    title: str
    context: str
    class_id: int
    section_id: int
    posted_by: int
    target_audience_id: int
    is_active: bool


class notice_boardresponse(BaseModel):
    id: int
    title: str
    context: str
    class_id: int
    section_id: int
    posted_by: int
    posted_at: date
    target_audience_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ============ STUDY MATERIAL ============
class study_materialcreate(BaseModel):
    class_id: int
    subject_id: int
    section_id: int
    teacher_id: int
    title: str
    description: str
    file_path: str


class study_materialresponse(BaseModel):
    id: int
    class_id: int
    subject_id: int
    section_id: int
    teacher_id: int
    title: str
    description: str
    file_path: str
    uploaded_at: date

    class Config:
        from_attributes = True


# ============ CONCESSION ============
class concessioncreate(BaseModel):
    student_id: int
    user_id: int
    academic_year_id: int
    concession_type: str
    concession_value: int
    reason: str


class concessionresponse(BaseModel):
    id: int
    student_id: int
    user_id: int
    academic_year_id: int
    concession_type: str
    concession_value: int
    reason: str
    granted_at: date

    class Config:
        from_attributes = True


# ============ ASSIGNMENT ============
class assignmentcreate(BaseModel):
    student_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: str
    deadline: date
    file_path: Optional[str] = None

    class Config:
        from_attributes = True


class assignmentresponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    teacher_id: int
    title: str
    description: str
    deadline: date
    created_at: date

    class Config:
        from_attributes = True


# ============ ACADEMIC YEARS ============
class academic_yearscreate(BaseModel):
    year: str
    start_date: date
    end_date: date


class academic_yearsresponse(BaseModel):
    id: int
    year: str
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


# ============ SCHOOL SETTINGS ============
class school_settingscreate(BaseModel):
    setting_key: str
    setting_value: str


class school_settingsresponse(BaseModel):
    id: int
    setting_key: str
    setting_value: str

    class Config:
        from_attributes = True