import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "school_db"),
    "user": os.getenv("DB_USER", "school_admin"),
    "password": os.getenv("DB_PASSWORD", "school123"),
    "port": os.getenv("DB_PORT", "5432")
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