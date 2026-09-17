from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from utils.dependencies import get_current_user
import subprocess
import os
from datetime import datetime
from io import BytesIO

router = APIRouter(prefix="/backup", tags=["Backup"])


@router.get("/database")
def download_database_backup(current_user: dict = Depends(get_current_user)):
    """Database ka SQL dump download karo."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can download backup")

    # Railway ka DATABASE_URL lo
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        # pg_dump se database export karo
        result = subprocess.run(
            ["pg_dump", database_url, "--no-owner", "--no-acl"],
            capture_output=True,
            check=True,
        )

        # BytesIO mein wrap karo
        buffer = BytesIO(result.stdout)
        buffer.seek(0)

        filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        return StreamingResponse(
            buffer,
            media_type="application/sql",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {e.stderr.decode()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup error: {str(e)}")