from database.db import get_db_connection, get_dict_cursor
from services.whatsapp_service import send_whatsapp
import os
import secrets


def create_guardian(user_id: int, student_id: int, full_name: str, relation: str,
                    phone_number: str, email: str, address: str, school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO guardians (user_id, student_id, full_name, relation, phone_number, email, address) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (user_id, student_id, full_name, relation, phone_number, email, address)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()

    result = {
        "id": new_id,
        "user_id": user_id,
        "student_id": student_id,
        "full_name": full_name,
        "relation": relation,
        "phone_number": phone_number,
        "email": email,
        "address": address
    }

    if school_id:
        try:
            send_guardian_welcome(new_id, school_id)
        except Exception as e:
            print(f"Welcome message failed: {e}")

    return result


def create_guardian_auto(student_id: int, full_name: str, relation: str,
                         phone_number: str, email: str, address: str,
                         school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing = cursor.fetchone()

    if existing:
        user_id = existing["id"]
    else:
        temp_password = secrets.token_urlsafe(8)
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, 'parent') RETURNING id",
            (full_name, email, temp_password)
        )
        user_id = cursor.fetchone()["id"]

    cursor.execute(
        "INSERT INTO guardians (user_id, student_id, full_name, relation, phone_number, email, address) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (user_id, student_id, full_name, relation, phone_number, email, address)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()

    result = {
        "id": new_id,
        "user_id": user_id,
        "student_id": student_id,
        "full_name": full_name,
        "relation": relation,
        "phone_number": phone_number,
        "email": email,
        "address": address
    }

    if school_id:
        try:
            send_guardian_welcome(new_id, school_id)
        except Exception as e:
            print(f"Welcome message failed: {e}")

    return result


def get_guardians_by_student(student_id: int):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "SELECT id, user_id, student_id, full_name, relation, phone_number, email, address FROM guardians WHERE student_id = %s ORDER BY id",
        (student_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "user_id": row["user_id"],
            "student_id": row["student_id"],
            "full_name": row["full_name"],
            "relation": row["relation"],
            "phone_number": row["phone_number"],
            "email": row["email"],
            "address": row["address"]
        }
        for row in rows
    ]


def send_guardian_welcome(guardian_id: int, school_id: int = None):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("""
        SELECT 
            g.id AS guardian_id,
            g.full_name AS guardian_name,
            g.relation,
            g.phone_number,
            g.whatsapp_number,
            s.roll_number,
            c.name AS class_name,
            sec.name AS section_name,
            u.full_name AS student_name
        FROM guardians g
        JOIN students s ON s.id = g.student_id
        JOIN users u ON u.id = s.user_id
        LEFT JOIN classes c ON c.id = s.class_id
        LEFT JOIN sections sec ON sec.id = s.section_id
        WHERE g.id = %s
    """, (guardian_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"success": False, "error": "Guardian not found"}

    parent_phone = row["whatsapp_number"] or row["phone_number"]
    student_name = row["student_name"] or "Student"
    class_name = row["class_name"] or ""
    section_name = row["section_name"] or ""
    roll_no = row["roll_number"] or "-"
    guardian_name = row["guardian_name"] or ""
    school_name = os.getenv("SCHOOL_NAME", "School")

    class_display = f"{class_name} ({section_name})" if section_name else class_name

    message = f"""Assalam o Alaikum {guardian_name}!

Aap ka bacha *{student_name}* (Roll No {roll_no}, Class {class_display}) school mein successfully add ho gaya hai.

Ab aap 24/7 school assistant se pooch sakte ho:
- Attendance
- Homework & Assignments
- Marks & Results
- Fees
- Timetable & Exams
- Notices

Bas WhatsApp par sawal bhejein - foran jawab milega!

- {school_name}"""

    result = send_whatsapp(school_id, parent_phone, message)
    print(f"Welcome message to {parent_phone}: {result}")
    return result
