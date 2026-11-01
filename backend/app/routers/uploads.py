import os
import secrets
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/uploads", tags=["File Uploads"])

UPLOAD_ROOT = settings.upload_path


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    sub_folder = "misc"
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    os.makedirs(UPLOAD_ROOT / sub_folder, exist_ok=True)
    filename = f"{secrets.token_hex(12)}{suffix}"
    file_path = UPLOAD_ROOT / sub_folder / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/api/uploads/{sub_folder}/{filename}",
        "filename": filename
    }


@router.get("/{folder}/{filename}")
def get_uploaded_file(folder: str, filename: str):
    root = UPLOAD_ROOT.resolve()
    file_path = (root / folder / filename).resolve()
    if not file_path.is_relative_to(root):
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
