import psycopg2
import psycopg2.extras
import os

# ✅ Railway DATABASE_URL check karo pehle (PgBouncer)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway (ya koi bhi cloud) — single URL se connect
    DB_CONFIG = {
        "dsn": DATABASE_URL,
        "sslmode": "require"
    }
else:
    # Local development
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "school_db"),
        "user": os.getenv("DB_USER", "school_admin"),
        "password": os.getenv("DB_PASSWORD", "school123"),
        "port": os.getenv("DB_PORT", "5432")
    }


def get_db_connection():
    """Database connection banao."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise e


def get_dict_cursor(conn):
    """Dict cursor — rows ko dict ki tarah return karega."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    """Database schema initialize karo."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        schema_path = os.path.join(os.path.dirname(__file__), 'schema_postgres.sql')
        with open(schema_path, 'r') as f:
            cursor.execute(f.read())
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise e