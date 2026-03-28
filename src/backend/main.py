import os
import shutil
from typing import Annotated
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CORS Configuration ---
# This allows the Streamlit frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DescriptionRequest(BaseModel):
    text: str
    address: str
    filename:str

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    file_path = os.path.join(UPLOAD_DIR, "latest_bytes_upload.bin")
    with open(file_path, "wb") as f:
        f.write(file)
    return {"file_size": len(file), "saved_as": "latest_bytes_upload.bin"}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "status": "Saved successfully"}

@app.post("/imageDescription")
async def give_description(req: DescriptionRequest):
    # Here is where you would normally call your VLM logic
    return {"description": req.text,
            "address":req.address,
            "filename": req.filename}

@app.get("/view/{filename}")
async def view_image(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found on server.")
        
    return FileResponse(file_path)