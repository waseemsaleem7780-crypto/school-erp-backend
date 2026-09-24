import cloudinary.uploader
from utils.cloudinary_config import cloudinary


def upload_file(file, folder: str = "school_erp"):
    """
    File ko Cloudinary par upload karo.
    
    - PDF, DOC, DOCX → resource_type="raw" (restriction nahi)
    - Images → resource_type="image"
    """
    try:
        # ✅ File type detect karo
        content_type = file.content_type or ""
        
        # PDF, DOC, DOCX → raw type
        if content_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            resource_type = "raw"
        else:
            resource_type = "image"   # JPG, PNG
        
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type=resource_type,   # ✅ Sahi type
        )
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "size": result.get("bytes"),
        }
    except Exception as e:
        print(f"Upload error: {e}")
        return None


def delete_file(public_id: str):
    """Cloudinary se file delete karo"""
    try:
        # ✅ Raw aur image dono try karo
        result = cloudinary.uploader.destroy(public_id, resource_type="raw")
        if result.get("result") != "ok":
            result = cloudinary.uploader.destroy(public_id, resource_type="image")
        return result
    except Exception as e:
        print(f"Delete error: {e}")
        return None