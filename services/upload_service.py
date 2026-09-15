import cloudinary.uploader
from utils.cloudinary_config import cloudinary


def upload_file(file, folder: str = "school_erp"):
    """
    File ko Cloudinary par upload karo.
    
    Input:
        file: FastAPI UploadFile object
        folder: Cloudinary folder name (jaise 'assignments', 'study_material')
    
    Output:
        {
            "url": "https://res.cloudinary.com/...",
            "public_id": "school_erp/abc123",
            "format": "pdf",
            "size": 12345
        }
    """
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="auto"
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
        result = cloudinary.uploader.destroy(public_id)
        return result
    except Exception as e:
        print(f"Delete error: {e}")
        return None