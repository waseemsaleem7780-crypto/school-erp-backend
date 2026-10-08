"""
Agent Tools — Parent Agent ke saare data functions.
LLM in functions ko call karega apne aap.
"""
from database.db import get_db_connection, get_dict_cursor
from datetime import date, datetime, timedelta


# ═══════════════════════════════════════════════
# 1. GUARDIAN / STUDENT LOOKUP
# ═══════════════════════════════════════════════

def get_guardian_by_phone(phone: str):
    """Phone se guardian dhundo (login/auth ke liye)."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT g.id, g.user_id, g.student_id, g.full_name, g.relation,
               g.phone_number, g.whatsapp_number, g.email, g.is_verified,
               s.roll_number, s.class_id, s.section_id,
               u.full_name AS student_name
        FROM guardians g
        JOIN students s ON s.id = g.student_id
        JOIN users u ON u.id = s.user_id
        WHERE g.phone_number = %s OR g.whatsapp_number = %s
        LIMIT 1
    """, (phone, phone))
    row = cur.fetchone()
    conn.close()
    return row


def get_student_info(student_id: int):
    """Student ki basic info."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT s.id, s.roll_number, s.class_id, s.section_id,
               u.full_name, u.email,
               c.name AS class_name,
               sec.name AS section_name
        FROM students s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN classes c ON c.id = s.class_id
        LEFT JOIN sections sec ON sec.id = s.section_id
        WHERE s.id = %s
    """, (student_id,))
    row = cur.fetchone()
    conn.close()
    return row


# ═══════════════════════════════════════════════
# 2. ATTENDANCE
# ═══════════════════════════════════════════════

def get_attendance_recent(student_id: int, days: int = 7):
    """Last N din ki attendance."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT date, status
        FROM attendance
        WHERE student_id = %s
          AND date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date DESC
    """, (student_id, days))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_attendance_summary(student_id: int, month: int = None, year: int = None):
    """Attendance percentage — is mahine ya overall."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    
    if month and year:
        cur.execute("""
            SELECT 
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE LOWER(status) = 'present') AS present,
                COUNT(*) FILTER (WHERE LOWER(status) = 'absent') AS absent,
                COUNT(*) FILTER (WHERE LOWER(status) = 'leave') AS leave
            FROM attendance
            WHERE student_id = %s
              AND EXTRACT(MONTH FROM date) = %s
              AND EXTRACT(YEAR FROM date) = %s
        """, (student_id, month, year))
    else:
        cur.execute("""
            SELECT 
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE LOWER(status) = 'present') AS present,
                COUNT(*) FILTER (WHERE LOWER(status) = 'absent') AS absent,
                COUNT(*) FILTER (WHERE LOWER(status) = 'leave') AS leave
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
    
    row = cur.fetchone()
    conn.close()
    
    if row and row["total"] and row["total"] > 0:
        row["percentage"] = round((row["present"] / row["total"]) * 100, 1)
    else:
        row["percentage"] = 0
    return row


def get_attendance_by_date(student_id: int, target_date: str):
    """Ek khaas din ki attendance."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT date, status, marked_at
        FROM attendance
        WHERE student_id = %s AND date = %s
    """, (student_id, target_date))
    row = cur.fetchone()
    conn.close()
    return row


# ═══════════════════════════════════════════════
# 3. MARKS / RESULTS
# ═══════════════════════════════════════════════

def get_marks(student_id: int):
    """Saare exam ke marks."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT r.id, r.marks_obtained, r.grade, r.remarks,
               e.name AS exam_name, e.exam_date, e.total_marks,
               sub.name AS subject_name
        FROM results r
        JOIN exam e ON e.id = r.exam_id
        JOIN subjects sub ON sub.id = r.subject_id
        WHERE r.student_id = %s
        ORDER BY e.exam_date DESC
    """, (student_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_marks_by_subject(student_id: int, subject_name: str):
    """Ek subject ke marks."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT r.marks_obtained, r.grade, r.remarks,
               e.name AS exam_name, e.exam_date, e.total_marks,
               sub.name AS subject_name
        FROM results r
        JOIN exam e ON e.id = r.exam_id
        JOIN subjects sub ON sub.id = r.subject_id
        WHERE r.student_id = %s AND LOWER(sub.name) LIKE LOWER(%s)
        ORDER BY e.exam_date DESC
    """, (student_id, f"%{subject_name}%"))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 4. HOMEWORK
# ═══════════════════════════════════════════════

def get_homework(student_id: int, days: int = 7):
    """Recent homework."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT h.id, h.title, h.description, h.deadline, h.created_at,
               h.file_path, sub.name AS subject_name,
               u.full_name AS teacher_name
        FROM homework h
        LEFT JOIN subjects sub ON sub.id = h.subject_id
        LEFT JOIN teachers t ON t.id = h.teacher_id
        LEFT JOIN users u ON u.id = t.user_id
        WHERE h.student_id = %s
          AND h.created_at >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY h.created_at DESC
    """, (student_id, days))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 5. ASSIGNMENTS
# ═══════════════════════════════════════════════

def get_assignments(student_id: int, days: int = 7):
    """Recent assignments."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT a.id, a.title, a.description, a.deadline, a.created_at,
               a.file_path, sub.name AS subject_name,
               u.full_name AS teacher_name
        FROM assignment a
        LEFT JOIN subjects sub ON sub.id = a.subject_id
        LEFT JOIN teachers t ON t.id = a.teacher_id
        LEFT JOIN users u ON u.id = t.user_id
        WHERE a.student_id = %s
          AND a.created_at >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY a.created_at DESC
    """, (student_id, days))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 6. FEES
# ═══════════════════════════════════════════════

def get_fee_payments(student_id: int):
    """Fee payment history."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    cur.execute("""
        SELECT id, monthly_fee, yearly_fee, amount,
               payment_date, payment_mod
        FROM fee_payment
        WHERE student_id = %s
        ORDER BY payment_date DESC
    """, (student_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 7. TIMETABLE
# ═══════════════════════════════════════════════

def get_timetable(class_id: int, section_id: int = None):
    """Class ka timetable."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    if section_id:
        cur.execute("""
            SELECT t.day_of_week, t.start_time, t.end_time,
                   sub.name AS subject_name,
                   u.full_name AS teacher_name
            FROM timetable t
            LEFT JOIN subjects sub ON sub.id = t.subject_id
            LEFT JOIN teachers tc ON tc.id = t.teacher_id
            LEFT JOIN users u ON u.id = tc.user_id
            WHERE t.class_id = %s AND t.section_id = %s
            ORDER BY 
                CASE t.day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                END,
                t.start_time
        """, (class_id, section_id))
    else:
        cur.execute("""
            SELECT t.day_of_week, t.start_time, t.end_time,
                   sub.name AS subject_name,
                   u.full_name AS teacher_name
            FROM timetable t
            LEFT JOIN subjects sub ON sub.id = t.subject_id
            LEFT JOIN teachers tc ON tc.id = t.teacher_id
            LEFT JOIN users u ON u.id = tc.user_id
            WHERE t.class_id = %s
            ORDER BY 
                CASE t.day_of_week
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                END,
                t.start_time
        """, (class_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 8. NOTICES
# ═══════════════════════════════════════════════

def get_notices(class_id: int, section_id: int = None, limit: int = 10):
    """Class ke notices."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    if section_id:
        cur.execute("""
            SELECT id, title, context, posted_at
            FROM notice_board
            WHERE class_id = %s AND is_active = TRUE
              AND (section_id = %s OR section_id IS NULL)
            ORDER BY posted_at DESC
            LIMIT %s
        """, (class_id, section_id, limit))
    else:
        cur.execute("""
            SELECT id, title, context, posted_at
            FROM notice_board
            WHERE class_id = %s AND is_active = TRUE
            ORDER BY posted_at DESC
            LIMIT %s
        """, (class_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 9. EXAMS
# ═══════════════════════════════════════════════

def get_exams(class_id: int, upcoming_only: bool = True):
    """Class ke exams."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    if upcoming_only:
        cur.execute("""
            SELECT e.id, e.name, e.exam_date, e.total_marks, e.passing_marks,
                   sub.name AS subject_name
            FROM exam e
            LEFT JOIN subjects sub ON sub.id = e.subject_id
            WHERE e.class_id = %s AND e.exam_date >= CURRENT_DATE
            ORDER BY e.exam_date
        """, (class_id,))
    else:
        cur.execute("""
            SELECT e.id, e.name, e.exam_date, e.total_marks, e.passing_marks,
                   sub.name AS subject_name
            FROM exam e
            LEFT JOIN subjects sub ON sub.id = e.subject_id
            WHERE e.class_id = %s
            ORDER BY e.exam_date DESC
        """, (class_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 10. STUDY MATERIAL
# ═══════════════════════════════════════════════

def get_study_materials(class_id: int, section_id: int = None, limit: int = 10):
    """Study material list."""
    conn = get_db_connection()
    cur = get_dict_cursor(conn)
    if section_id:
        cur.execute("""
            SELECT sm.id, sm.title, sm.description, sm.file_path,
                   sm.uploaded_at, sub.name AS subject_name
            FROM study_material sm
            LEFT JOIN subjects sub ON sub.id = sm.subject_id
            WHERE sm.class_id = %s AND (sm.section_id = %s OR sm.section_id IS NULL)
            ORDER BY sm.uploaded_at DESC
            LIMIT %s
        """, (class_id, section_id, limit))
    else:
        cur.execute("""
            SELECT sm.id, sm.title, sm.description, sm.file_path,
                   sm.uploaded_at, sub.name AS subject_name
            FROM study_material sm
            LEFT JOIN subjects sub ON sub.id = sm.subject_id
            WHERE sm.class_id = %s
            ORDER BY sm.uploaded_at DESC
            LIMIT %s
        """, (class_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════
# 11. LOG
# ═══════════════════════════════════════════════

def log_agent_interaction(guardian_id, student_id, question, answer, intent, tools_used, response_ms):
    """Har sawal/jawab log karo."""
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)
        cur.execute("""
            INSERT INTO agent_logs 
            (guardian_id, student_id, question, answer, intent, tools_used, response_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (guardian_id, student_id, question, answer, intent, tools_used, response_ms))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log failed: {e}")


# ═══════════════════════════════════════════════
# TOOLS SCHEMA — LLM ko batane ke liye (OpenAI format)
# ═══════════════════════════════════════════════

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_student_info",
            "description": "Student ki basic info (naam, class, section, roll number)",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer", "description": "Student ID"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_recent",
            "description": "Last N din ki attendance (default 7)",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "days": {"type": "integer", "description": "Kitne din pehle tak (default 7)"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_summary",
            "description": "Attendance percentage aur total present/absent",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "month": {"type": "integer", "description": "1-12 (optional)"},
                    "year": {"type": "integer", "description": "e.g. 2026 (optional)"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_by_date",
            "description": "Ek khaas din ki attendance",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "target_date": {"type": "string", "description": "YYYY-MM-DD format"}
                },
                "required": ["student_id", "target_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_marks",
            "description": "Saare exam ke marks",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_marks_by_subject",
            "description": "Ek subject ke marks",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "subject_name": {"type": "string", "description": "e.g. Math, English"}
                },
                "required": ["student_id", "subject_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_homework",
            "description": "Recent homework",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "days": {"type": "integer"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_assignments",
            "description": "Recent assignments",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"},
                    "days": {"type": "integer"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fee_payments",
            "description": "Fee payment history",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "integer"}
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_timetable",
            "description": "Class ka timetable",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer"},
                    "section_id": {"type": "integer"}
                },
                "required": ["class_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notices",
            "description": "Class ke notices",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer"},
                    "section_id": {"type": "integer"},
                    "limit": {"type": "integer"}
                },
                "required": ["class_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exams",
            "description": "Class ke exams",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer"},
                    "upcoming_only": {"type": "boolean"}
                },
                "required": ["class_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_materials",
            "description": "Study material list",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer"},
                    "section_id": {"type": "integer"},
                    "limit": {"type": "integer"}
                },
                "required": ["class_id"]
            }
        }
    },
]


# ═══════════════════════════════════════════════
# TOOL DISPATCHER — LLM ke tool call ko function se connect karo
# ═══════════════════════════════════════════════

TOOL_FUNCTIONS = {
    "get_student_info": get_student_info,
    "get_attendance_recent": get_attendance_recent,
    "get_attendance_summary": get_attendance_summary,
    "get_attendance_by_date": get_attendance_by_date,
    "get_marks": get_marks,
    "get_marks_by_subject": get_marks_by_subject,
    "get_homework": get_homework,
    "get_assignments": get_assignments,
    "get_fee_payments": get_fee_payments,
    "get_timetable": get_timetable,
    "get_notices": get_notices,
    "get_exams": get_exams,
    "get_study_materials": get_study_materials,
}


def execute_tool(tool_name: str, args: dict):
    """LLM ke request par function chalao."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        result = func(**args)
        return result
    except Exception as e:
        return {"error": str(e)}
