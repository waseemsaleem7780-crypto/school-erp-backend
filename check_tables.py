import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DB_CONFIG = {"dsn": DATABASE_URL, "sslmode": "require"}
else:
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "school_db"),
        "user": os.getenv("DB_USER", "school_admin"),
        "password": os.getenv("DB_PASSWORD", "school123"),
        "port": os.getenv("DB_PORT", "5432"),
    }

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

tables = ['attendance', 'results', 'exam', 'homework', 'assignment', 
          'fee_payment', 'notice_board', 'timetable', 'study_material']

for tbl in tables:
    print(f"\n===== {tbl} =====")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (tbl,))
    for row in cursor.fetchall():
        print(f"   {row[0]} ({row[1]})")

cursor.close()
conn.close()
