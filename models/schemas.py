from pydantic import BaseModel, EmailStr, validator
from datetime import date
from typing import Optional


class userlogin(BaseModel):
    email: str
    password: str 

    
class usercreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str

    @validator('role')
    def validate_role(cls, v):
        v = v.lower()
        if v not in (['admin','teacher','student','parent']):
            raise ValueError('Role must be one of: admin, teacher, student, parent')
        return v

class userresponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    created_at: date

    class Config:
        from_attributes = True


class classescreate(BaseModel):
    name : str

class classesresponse(BaseModel):
    id :int
    name : str

    class Config:
        from_attributes = True

class sectionscreate(BaseModel):
    name : str
    class_id : int


class sectionsresponse(BaseModel):
    id : int
    name : str
    class_id :int

    class Config:
        from_attributes = True

class subjectscreate(BaseModel):
    name : str
    code : str
    class_id : int

class subjectsresponse(BaseModel):
    id : int
    name : str
    code : str
    class_id : int

    class Config:
        from_attributes = True


class teacherscreate(BaseModel):
    user_id : int
    qualification : str

class teachersresponse(BaseModel):
    id : int
    user_id : int
    qualification : str
    hired_date : date

    class Config:
        from_attributes = True


class fee_structurecreate(BaseModel):
    class_id : int
    month : int
    yearly_fee : int
    amount : int
    due_date : date

class fee_structureresponse(BaseModel):
    id : int
    class_id : int
    month : int
    yearly_fee : int
    amount : int
    due_date : date

    class Config:
        from_attributes = True

class fee_paymentcreate(BaseModel):
    student_id : int
    monthly_fee : int
    yearly_fee : int
    amount : int
    payment_mod : str


class fee_paymentresponse(BaseModel):
    id : int
    student_id : int
    monthly_fee : int
    yearly_fee : int
    amount : int
    payment_date : date
    payment_mod : str

    class Config:
        from_attributes = True

class homeworkcreate(BaseModel):
    student_id : int
    subject_id : int
    teacher_id : int
    title : str
    description : str
    deadline : date

class homeworkresponse(BaseModel):
    id : int
    student_id : int
    subject_id : int
    teacher_id : int
    title : str
    description : str
    deadline : date
    created_at : date

    class Config:
        from_attributes = True


class examcreate(BaseModel):
    name : str
    class_id : int
    subject_id : int
    exam_date : date
    total_marks : int
    passing_marks : int

class examresponse(BaseModel):
    id : int
    name : str
    class_id : int
    subject_id : int
    exam_date : date
    total_marks : int
    passing_marks : int

    class Config:
        from_attributes = True

class resultcreate(BaseModel):
    exam_id : int
    student_id : int
    subject_id : int
    marks_obtained : int
    grade : str
    remarks : str

class resultresponse(BaseModel):
    id : int
    exam_id : int
    student_id : int
    subject_id : int
    marks_obtained : int
    grade : str
    remarks : str

    class Config:
        from_attributes = True

class students(BaseModel):
    user_id : int
    class_id : int
    section_id : int
    roll_number : str

class studentsresponse(BaseModel):
    id : int
    user_id : int
    class_id : int
    section_id : int
    roll_number : str

    class Config:
        from_attributes = True

class attendancecreate(BaseModel):
    student_id : int
    date : date
    status : str
    marked_by : int

    @validator('status')
    def validate_status(cls, v):
        v = v.lower()
        if v not in (['present','absent','half_day','leave']):
            raise ValueError("Invalid status value")
        return v

class attendanceresponse(BaseModel):
    id : int
    student_id : int
    date : date
    status : str
    marked_by : int
    marked_at : date

    class Config:
        from_attributes = True

class guardianscreate(BaseModel):
    user_id : int
    student_id : int
    full_name : str
    relation : str 
    phone_number : str
    email : EmailStr    
    address : str

    @validator('relation')
    def validate_relation(cls,v):
        v = v.lower()
        if v not in (['father','mother','guardian']):
            raise ValueError("Invalid relation value")
        return v
    
class guardiansresponse(BaseModel):
    id : int
    user_id : int
    student_id : int
    full_name : str
    relation : str 
    phone_number : str
    email : EmailStr    
    address : str
    
    class Config:
        from_attributes = True


class timetablecreate(BaseModel):
    class_id : int
    section_id : int
    subject_id : int
    teacher_id : int
    day_of_week : str
    start_time : str
    end_time : str


    @validator('day_of_week')
    def validate_day_of_week(cls,v):
        v = v.lower()
        if v not in (['monday','tuesday','wednesday','thursday','friday','saturday']):
            raise ValueError("Invalid day of week value")
        return v

class timetableresponse(BaseModel):
    id : int
    class_id : int
    section_id : int
    subject_id : int
    teacher_id : int
    day_of_week : str
    start_time : str
    end_time : str

    class Config:
        from_attributes = True


class notice_boardcreate(BaseModel):
    title : str
    context : str
    class_id : int
    section_id : int
    posted_by : int
    target_audience_id : int
    is_active : bool

class notice_boardresponse(BaseModel):
    id : int
    title : str
    context : str
    class_id : int
    section_id : int
    posted_by : int
    posted_at : date
    target_audience_id : int
    is_active : bool

    class Config:
        from_attributes = True

class study_materialcreate(BaseModel):
    class_id : int
    subject_id : int
    section_id : int
    teacher_id : int
    title : str
    description : str
    file_path : str

class study_materialresponse(BaseModel):
    id : int
    class_id : int
    subject_id : int
    section_id : int
    teacher_id : int
    title : str
    description : str
    file_path : str
    uploaded_at : date

    class Config:
        from_attributes = True

class concessioncreate(BaseModel):

    student_id : int
    user_id : int
    academic_year_id : int
    concession_type : str
    concession_value : int
    reason : str

class concessionresponse(BaseModel):
    id : int
    student_id : int
    user_id : int
    academic_year_id : int
    concession_type : str
    concession_value : int
    reason : str
    granted_at : date

    class Config:
        from_attributes = True

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
    id : int
    student_id : int
    subject_id : int
    teacher_id : int    
    title : str
    description : str
    deadline : date
    created_at : date

    class Config:
        from_attributes = True

class academic_yearscreate(BaseModel):
    year : str
    start_date : date
    end_date : date

class academic_yearsresponse(BaseModel):
    id : int
    year : str
    start_date : date
    end_date : date

    class Config:
        from_attributes = True

class school_settingscreate(BaseModel):
    setting_key : str
    setting_value : str

class school_settingsresponse(BaseModel):
    id : int
    setting_key : str
    setting_value : str

    class Config:
        from_attributes = True
