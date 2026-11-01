import os
import random
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/uploads", tags=["File Uploads"])

UPLOAD_ROOT = "backend/uploads"


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    sub_folder = "misc"
    os.makedirs(os.path.join(UPLOAD_ROOT, sub_folder), exist_ok=True)
    filename = f"{random.randint(1000, 9999)}_{file.filename}"
    file_path = os.path.join(UPLOAD_ROOT, sub_folder, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/api/uploads/{sub_folder}/{filename}",
        "filename": filename
    }


@router.get("/{folder}/{filename}")
def get_uploaded_file(folder: str, filename: str):
    file_path = os.path.join(UPLOAD_ROOT, folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

