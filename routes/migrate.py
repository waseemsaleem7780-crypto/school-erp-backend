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
