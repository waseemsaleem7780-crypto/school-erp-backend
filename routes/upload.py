from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from services.upload_service import upload_file, delete_file
from utils.dependencies import get_current_user

router = APIRouter(prefix="/upload", tags=["File Upload"])


@router.post("/file")
async def upload_single_file(
    file: UploadFile = File(...),
    folder: str = Form("school_erp"),
    current_user: dict = Depends(get_current_user),
):
    """File upload karo (Cloudinary par)"""
    
    # Sirf teacher aur admin upload kar sakte hain
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can upload")
    
    # File type check karo
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: PDF, JPG, PNG, DOC, DOCX"
        )
    
    result = upload_file(file, folder)
    
    if not result:
        raise HTTPException(status_code=500, detail="Upload failed")
    
    return {
        "message": "File uploaded successfully",
        "url": result["url"],
        "public_id": result["public_id"],
        "format": result["format"],
        "size": result["size"],
    }


@router.delete("/file/{public_id:path}")
async def delete_uploaded_file(
    public_id: str,
    current_user: dict = Depends(get_current_user),
):
    """File delete karo (Cloudinary se)"""
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can delete")
    
    result = delete_file(public_id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Delete failed")
    
    return {"message": "File deleted successfully", "result": result}