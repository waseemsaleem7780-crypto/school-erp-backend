import os
import psycopg2

# Database connection (aap ke db.py jaisa)
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

print("🔄 Connecting to database...")
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cursor = conn.cursor()

# Migration file padho
with open("database/agent_migration.sql", "r") as f:
    sql = f.read()

print("🔄 Running migration...")
try:
    cursor.execute(sql)
    print("✅ Migration successful!")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()

# Verify
print("\n🔄 Verifying guardians table columns...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'guardians'
    ORDER BY ordinal_position
""")
print("\n📋 Guardians table columns:")
for row in cursor.fetchall():
    print(f"   - {row[0]} ({row[1]})")

# Check agent_logs
cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_name IN ('agent_logs', 'agent_settings')
""")
print("\n📋 New tables:")
for row in cursor.fetchall():
    print(f"   - {row[0]}")

cursor.close()
conn.close()
print("\n🎉 Done!")
