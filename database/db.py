import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    "host": "localhost",
    "database": "school_db",
    "user": "school_admin",
    "password": "school123",
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def get_dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema_postgres.sql')
    with open(schema_path, 'r') as f:
        cursor.execute(f.read())
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL Database initialized successfully!")