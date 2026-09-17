from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from utils.dependencies import get_current_user
import os
import subprocess
import shutil
from datetime import datetime
from io import BytesIO

router = APIRouter(prefix="/backup", tags=["Backup"])


def get_database_url():
    """DATABASE_URL banao — env vars se."""
    # Pehle DATABASE_URL try karo
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Fallback: DB_HOST, DB_NAME, etc. se banao
    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "railway")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "5432")

    if not password:
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@router.get("/database")
def download_database_backup(current_user: dict = Depends(get_current_user)):
    """Database ka SQL dump download karo."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can download backup")

    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=500,
            detail="Database configuration missing. Need DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD."
        )

    print(f"Database URL: {database_url[:30]}...")

    # pg_dump ka full path dhoondo
    pg_dump_path = shutil.which("pg_dump")
    if not pg_dump_path:
        # Common paths try karo
        for path in ["/usr/bin/pg_dump", "/usr/local/bin/pg_dump"]:
            if os.path.exists(path):
                pg_dump_path = path
                break

    if not pg_dump_path:
        raise HTTPException(status_code=500, detail="pg_dump not found on server")

    print(f"pg_dump path: {pg_dump_path}")

    try:
        result = subprocess.run(
            [pg_dump_path, database_url, "--no-owner", "--no-acl"],
            capture_output=True,
            check=True,
            timeout=120,
        )

        buffer = BytesIO(result.stdout)
        buffer.seek(0)
        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        return StreamingResponse(
            buffer,
            media_type="application/sql",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"pg_dump error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {error_msg}")
    except Exception as e:
        print(f"backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Backup error: {str(e)}")