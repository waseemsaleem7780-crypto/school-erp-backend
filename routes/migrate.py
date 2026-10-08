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
