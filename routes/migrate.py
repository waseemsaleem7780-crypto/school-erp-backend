from fastapi import APIRouter, HTTPException
from database.db import get_db_connection, get_dict_cursor

router = APIRouter(prefix="/migrate", tags=["Migration"])


@router.post("/agent")
def run_agent_migration():
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = get_dict_cursor(conn)

        cur.execute("ALTER TABLE guardians ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20)")
        cur.execute("ALTER TABLE guardians ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE")
        cur.execute("ALTER TABLE guardians ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id SERIAL PRIMARY KEY,
                guardian_id INTEGER,
                student_id INTEGER,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent VARCHAR(100),
                tools_used TEXT,
                response_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_settings (
                id SERIAL PRIMARY KEY,
                school_id INTEGER NOT NULL UNIQUE,
                is_enabled BOOLEAN DEFAULT TRUE,
                welcome_message TEXT,
                language VARCHAR(20) DEFAULT 'ur',
                escalate_to_teacher BOOLEAN DEFAULT TRUE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'guardians'
            ORDER BY ordinal_position
        """)
        columns = [r["column_name"] for r in cur.fetchall()]
        conn.close()

        return {
            "success": True,
            "message": "Migration complete!",
            "guardians_columns": columns,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/seed-teacher-data")
def seed_teacher_data():
    """
    Railway production ke liye test data:
    - Subjects add karo
    - Timetable entries banao
    - Teacher ko classes assign karo
    """
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = get_dict_cursor(conn)

        # 1. Classes dekho
        cur.execute("SELECT id, name FROM classes ORDER BY id")
        classes = cur.fetchall()
        if not classes:
            return {"success": False, "error": "Koi class nahi hai"}

        class_id = classes[0]["id"]
        print(f"Using class_id: {class_id}")

        # 2. Teachers dekho
        cur.execute("SELECT id, user_id FROM teachers LIMIT 1")
        teacher = cur.fetchone()
        if not teacher:
            return {"success": False, "error": "Koi teacher nahi hai"}
        teacher_id = teacher["id"]
        print(f"Using teacher_id: {teacher_id}")

        # 3. Subjects check/add karo
        cur.execute("SELECT id, name FROM subjects WHERE class_id = %s", (class_id,))
        existing_subs = cur.fetchall()
        sub_ids = {s["name"]: s["id"] for s in existing_subs}

        needed_subs = ["Mathematics", "English", "Science"]
        for sub_name in needed_subs:
            if sub_name not in sub_ids:
                cur.execute(
                    "INSERT INTO subjects (name, code, class_id) VALUES (%s, %s, %s) RETURNING id",
                    (sub_name, sub_name[:3].upper(), class_id)
                )
                sub_ids[sub_name] = cur.fetchone()["id"]

        print(f"Subjects: {sub_ids}")

        # 4. Timetable clear + add karo
        cur.execute("DELETE FROM timetable WHERE class_id = %s", (class_id,))

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        periods = [('08:00', '09:00'), ('09:00', '10:00'), ('10:15', '11:15'), ('11:15', '12:15')]
        sub_names = ['Mathematics', 'English', 'Science', 'Mathematics']

        count = 0
        for day in days:
            for i, (start, end) in enumerate(periods):
                sub_id = sub_ids.get(sub_names[i])
                if not sub_id:
                    continue
                cur.execute("""
                    INSERT INTO timetable 
                    (class_id, section_id, subject_id, teacher_id, day_of_week, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (class_id, 1, sub_id, teacher_id, day, start, end))
                count += 1

        conn.close()

        return {
            "success": True,
            "message": "Teacher data seed complete!",
            "class_id": class_id,
            "teacher_id": teacher_id,
            "subjects": list(sub_ids.keys()),
            "timetable_entries": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/teacher-assignments")
def migrate_teacher_assignments():
    """
    Teachers table mein missing columns add karo + teacher_assignments table banao.
    Timetable se data populate karo.
    """
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = get_dict_cursor(conn)

        results = []

        # 1. teachers table mein columns add karo
        cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS school_id INTEGER DEFAULT 1")
        results.append("school_id added")

        cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")
        results.append("deleted_at added")

        cur.execute("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
        results.append("phone added")

        # 2. users table mein bhi school_id + phone (agar missing)
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS school_id INTEGER DEFAULT 1")
        results.append("users.school_id added")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
        results.append("users.phone added")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
        results.append("users.is_active added")

        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")
        results.append("users.deleted_at added")

        # 3. classes table mein school_id
        cur.execute("ALTER TABLE classes ADD COLUMN IF NOT EXISTS school_id INTEGER DEFAULT 1")
        results.append("classes.school_id added")

        # 4. subjects mein school_id
        cur.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS school_id INTEGER DEFAULT 1")
        results.append("subjects.school_id added")

        # 5. students mein school_id
        cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS school_id INTEGER DEFAULT 1")
        results.append("students.school_id added")

        # 6. teacher_assignments table banao
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_assignments (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                section_id INTEGER,
                subject_id INTEGER,
                school_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        results.append("teacher_assignments table created")

        # 7. Timetable se teacher assignments populate karo
        cur.execute("DELETE FROM teacher_assignments")
        cur.execute("""
            INSERT INTO teacher_assignments (teacher_id, class_id, section_id, subject_id, school_id)
            SELECT DISTINCT teacher_id, class_id, section_id, subject_id, 1
            FROM timetable
            WHERE teacher_id IS NOT NULL AND class_id IS NOT NULL
        """)
        cur.execute("SELECT COUNT(*) as cnt FROM teacher_assignments")
        count = cur.fetchone()["cnt"]
        results.append(f"{count} assignments populated from timetable")

        conn.close()

        return {
            "success": True,
            "message": "Teacher assignments migration complete!",
            "steps": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/student-parent-columns")
def add_student_parent_columns():
    """Students table mein parent_whatsapp + parent_name columns add karo + guardians se populate."""
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = get_dict_cursor(conn)

        results = []

        # 1. Columns add
        cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS parent_whatsapp VARCHAR(20)")
        results.append("parent_whatsapp added")

        cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS parent_name VARCHAR(255)")
        results.append("parent_name added")

        # 2. Guardians se populate karo
        cur.execute("""
            UPDATE students s
            SET parent_whatsapp = g.phone_number,
                parent_name = g.full_name
            FROM guardians g
            WHERE g.student_id = s.id
              AND (s.parent_whatsapp IS NULL OR s.parent_name IS NULL)
        """)
        results.append(f"{cur.rowcount} students updated from guardians")

        # 3. Verify
        cur.execute("""
            SELECT COUNT(*) as cnt FROM students 
            WHERE parent_whatsapp IS NOT NULL
        """)
        count = cur.fetchone()["cnt"]
        results.append(f"{count} students have parent contact")

        # 4. teacher_messages table check
        cur.execute("""
            CREATE TABLE IF NOT EXISTS teacher_messages (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER,
                student_id INTEGER,
                parent_phone VARCHAR(20),
                message TEXT,
                school_id INTEGER,
                status VARCHAR(50),
                whatsapp_message_id VARCHAR(100),
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        results.append("teacher_messages table created")

        conn.close()

        return {
            "success": True,
            "message": "Student parent columns migration complete!",
            "steps": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diagnose")
def diagnose_data():
    """Diagnose: classes, students, teachers, assignments sab check karo."""
    try:
        conn = get_db_connection()
        cur = get_dict_cursor(conn)

        result = {}

        # Classes
        cur.execute("SELECT id, name FROM classes ORDER BY id")
        result["classes"] = [dict(r) for r in cur.fetchall()]

        # Students per class
        cur.execute("""
            SELECT c.id as class_id, c.name as class_name, 
                   COUNT(s.id) as student_count
            FROM classes c
            LEFT JOIN students s ON s.class_id = c.id
            GROUP BY c.id, c.name
            ORDER BY c.id
        """)
        result["students_per_class"] = [dict(r) for r in cur.fetchall()]

        # Teacher assignments
        cur.execute("""
            SELECT ta.id, ta.teacher_id, ta.class_id, ta.section_id,
                   c.name as class_name, s.name as section_name
            FROM teacher_assignments ta
            LEFT JOIN classes c ON c.id = ta.class_id
            LEFT JOIN sections s ON s.id = ta.section_id
            ORDER BY ta.teacher_id
        """)
        result["teacher_assignments"] = [dict(r) for r in cur.fetchall()]

        # Sections
        cur.execute("SELECT id, name, class_id FROM sections ORDER BY class_id")
        result["sections"] = [dict(r) for r in cur.fetchall()]

        # Users (teachers)
        cur.execute("SELECT id, full_name, email, role FROM users WHERE role = 'teacher'")
        result["teachers_users"] = [dict(r) for r in cur.fetchall()]

        # Teachers table
        cur.execute("SELECT id, user_id FROM teachers")
        result["teachers_table"] = [dict(r) for r in cur.fetchall()]

        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
