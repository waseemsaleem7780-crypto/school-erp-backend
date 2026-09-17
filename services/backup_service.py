from database.db import get_db_connection, get_dict_cursor
import subprocess
import os
from datetime import datetime
from io import BytesIO


def generate_backup():
    """Database ka SQL dump generate karo."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None

    try:
        result = subprocess.run(
            ["pg_dump", database_url, "--no-owner", "--no-acl"],
            capture_output=True,
            check=True,
        )
        return result.stdout
    except Exception as e:
        print("backup error:", e)
        return None


def get_backup_stats():
    """Database ki size aur tables ki count."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    try:
        cursor.execute("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as db_size,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
        """)
        row = cursor.fetchone()
        return {
            "database_size": row["db_size"],
            "table_count": row["table_count"],
        }
    except Exception as e:
        print("stats error:", e)
        return {}
    finally:
        conn.close()