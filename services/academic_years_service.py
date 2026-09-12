from database.db import get_db_connection, get_dict_cursor

def create_academic_year(year: str, start_date: str, end_date: str):
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute(
        "INSERT INTO academic_years (year, start_date, end_date) VALUES (%s, %s, %s) RETURNING id",
        (year, start_date, end_date)
    )
    new_id = cursor.fetchone()["id"]
    conn.commit()
    conn.close()
    return {
        "id": new_id,
        "year": year,
        "start_date": start_date,
        "end_date": end_date
    }

def get_all_academic_years():
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT id, year, start_date, end_date FROM academic_years ORDER BY start_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "year": row["year"],
            "start_date": row["start_date"],
            "end_date": row["end_date"]
        }
        for row in rows
    ]