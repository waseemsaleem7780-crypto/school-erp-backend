from database.db import get_db_connection, get_dict_cursor
from services.whatsapp_service import send_whatsapp, log_notification


def get_student_parent_info(student_id: int, school_id: int):
    """Student aur parent ki info dhundo — seedha students table se."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        """SELECT 
               u.full_name as student_name,
               s.roll_number,
               c.name as class_name,
               sec.name as section_name,
               s.parent_whatsapp as parent_phone,
               s.parent_name as parent_name,
               sch.name as school_name
           FROM students s
           JOIN users u ON u.id = s.user_id
           JOIN schools sch ON sch.id = s.school_id
           LEFT JOIN classes c ON c.id = s.class_id
           LEFT JOIN sections sec ON sec.id = s.section_id
           WHERE s.id = %s AND s.school_id = %s LIMIT 1""",
        (student_id, school_id)
    )
    info = cursor.fetchone()
    conn.close()
    return dict(info) if info else None


def notify_absent(school_id: int, student_id: int, date: str):
    """Student absent hone par parent ko message."""
    info = get_student_parent_info(student_id, school_id)
    if not info or not info["parent_phone"]:
        return {"success": False, "error": "Parent phone not found"}

    message = f"""Assalam-o-Alaikum!

Aap ka bacha *{info['student_name']}* (Roll #{info['roll_number']}, {info['class_name'] or 'N/A'})
aaj school mein *GHAIR HAZIR* tha.

📅 Date: {date}

Shukriya,
{info['school_name']}"""

    result = send_whatsapp(school_id, info["parent_phone"], message)
    status = "sent" if result["success"] else "failed"
    log_notification(
        school_id, student_id, info["parent_phone"],
        "ABSENT", message, status,
        result.get("message_id"), result.get("error")
    )
    return result


def notify_homework_not_done(school_id: int, student_id: int, homework_title: str, subject_name: str):
    """Homework nahi kiya — parent ko message."""
    info = get_student_parent_info(student_id, school_id)
    if not info or not info["parent_phone"]:
        return {"success": False, "error": "Parent phone not found"}

    message = f"""Assalam-o-Alaikum!

Aap ke bache *{info['student_name']}* (Roll #{info['roll_number']})
ne aaj *{subject_name}* ka homework nahi kiya.

📝 Homework: {homework_title}

Baraye meharbani ghar par check karein.

Shukriya,
{info['school_name']}"""

    result = send_whatsapp(school_id, info["parent_phone"], message)
    status = "sent" if result["success"] else "failed"
    log_notification(
        school_id, student_id, info["parent_phone"],
        "HOMEWORK", message, status,
        result.get("message_id"), result.get("error")
    )
    return result


# ✅ NAYA FUNCTION — Result Notification
def notify_result(school_id: int, student_id: int, exam_name: str, 
                  subject_name: str, marks: int, total: int, grade: str):
    """Exam result aane par parent ko message."""
    info = get_student_parent_info(student_id, school_id)
    if not info or not info["parent_phone"]:
        return {"success": False, "error": "Parent phone not found"}

    percentage = round((marks / total) * 100, 2) if total > 0 else 0

    message = f"""Assalam-o-Alaikum!

*{info['student_name']}* (Roll #{info['roll_number']}) ka result aa gaya hai:

📝 Exam: {exam_name}
📚 Subject: {subject_name}
📊 Marks: {marks}/{total} ({percentage}%)
🏆 Grade: {grade}

Shukriya,
{info['school_name']}"""

    result = send_whatsapp(school_id, info["parent_phone"], message)
    status = "sent" if result["success"] else "failed"
    log_notification(
        school_id, student_id, info["parent_phone"],
        "RESULT", message, status,
        result.get("message_id"), result.get("error")
    )
    return result