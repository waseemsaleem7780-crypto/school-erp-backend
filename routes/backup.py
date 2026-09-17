from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from utils.dependencies import get_current_user
from database.db import get_db_connection, get_dict_cursor
from datetime import datetime
from io import BytesIO

router = APIRouter(prefix="/backup", tags=["Backup"])


@router.get("/database")
def download_database_backup(current_user: dict = Depends(get_current_user)):
    """Database ka backup download karo (pure Python — pg_dump ki zaroorat nahi)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can download backup")

    conn = get_db_connection()
    cursor = get_dict_cursor(conn)

    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    tables = [row["table_name"] for row in cursor.fetchall()]

    sql_lines = [
        "-- School ERP Database Backup",
        f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Total Tables: {len(tables)}",
        "",
        "SET statement_timeout = 0;",
        "SET client_encoding = 'UTF8';",
        "",
    ]

    for table in tables:
        sql_lines.append(f"\n-- ============================================")
        sql_lines.append(f"-- Table: {table}")
        sql_lines.append(f"-- ============================================\n")
        sql_lines.append(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

        cursor.execute(f'SELECT * FROM "{table}"')
        rows = cursor.fetchall()

        if not rows:
            sql_lines.append(f"-- (empty table)\n")
            continue

        columns = list(rows[0].keys())
        cols_str = ", ".join([f'"{c}"' for c in columns])

        sql_lines.append(f"-- Rows: {len(rows)}\n")
        for row in rows:
            values = []
            for v in row.values():
                if v is None:
                    values.append("NULL")
                elif isinstance(v, str):
                    values.append("'" + v.replace("'", "''") + "'")
                elif isinstance(v, (int, float)):
                    values.append(str(v))
                elif isinstance(v, bool):
                    values.append("TRUE" if v else "FALSE")
                else:
                    values.append("'" + str(v).replace("'", "''") + "'")
            sql_lines.append(f'INSERT INTO "{table}" ({cols_str}) VALUES ({", ".join(values)});')
        sql_lines.append("")

    conn.close()

    sql_content = "\n".join(sql_lines)
    buffer = BytesIO(sql_content.encode('utf-8'))
    buffer.seek(0)
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

    return StreamingResponse(
        buffer,
        media_type="application/sql",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )