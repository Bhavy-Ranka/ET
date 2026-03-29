import os
import sys
import shutil
from typing import Annotated
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import ComplaintDB, SessionLocal
from authentication import router as auth_router, get_current_user

# PYTHONPATH is set by run_app.py, so this just works
try:
    from gen_ai.ai_main import run_pipeline
    # fromfrom gen_ai.ai_main import run_pipeline
#  import run_pipeline  # PYTHONPATH set by run_app.py
    _PIPELINE_AVAILABLE = True
    print("ha bhai ho gai!!")
except Exception as _err:
    _PIPELINE_AVAILABLE = False
    print(f"[WARNING] gen_ai pipeline could not be imported: {_err}")

print("ndnwej")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class DescriptionRequest(BaseModel):
    text: str
    address: str
    filename: str


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    file_path = os.path.join(UPLOAD_DIR, "latest_bytes_upload.bin")
    with open(file_path, "wb") as f:
        f.write(file)
    return {"file_size": len(file), "saved_as": "latest_bytes_upload.bin"}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile, current_user: str = Depends(get_current_user)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "status": "Saved successfully"}


@app.post("/imageDescription")
async def give_description(req: DescriptionRequest, current_user: str = Depends(get_current_user)):
    # 1. Save complaint to SQLite DB
    db = SessionLocal()
    new_complaint = ComplaintDB(
        username=current_user,
        text=req.text,
        address=req.address,
        filename=req.filename,
    )
    db.add(new_complaint)
    db.commit()
    db.close()

    # 2. Run AI pipeline
    pipeline_result = {}
    pipeline_warning = None

    if not _PIPELINE_AVAILABLE:
        pipeline_warning = "Pipeline unavailable at startup; skipping."
    else:
        image_path = os.path.join(UPLOAD_DIR, req.filename)
        if not os.path.isfile(image_path):
            pipeline_warning = f"Image '{req.filename}' not found in uploads/; pipeline skipped."
        else:
            try:
                pipeline_result = run_pipeline(image_path, req.address, req.text)
            except Exception as exc:
                pipeline_warning = f"Pipeline error: {exc}"
                print(f"[ERROR] Pipeline failed: {exc}")

    response = {
        "status": "Complaint Saved",
        "description": req.text,
        "address": req.address,
        "pipeline": pipeline_result,
    }
    if pipeline_warning:
        response["pipeline_warning"] = pipeline_warning

    return response


@app.get("/view/{filename}")
async def view_image(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found on server.")
    return FileResponse(file_path)

@app.get("/admin/complaints")
async def get_all_complaints(current_user: str = Depends(get_current_user)):
    if current_user not in ["BHAVY", "SMARTYY"]:
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    
    try:
        from pymongo import MongoClient
        import os
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        db = client[os.getenv("MONGO_DB", "hack")]
        collection = db[os.getenv("MONGO_COLLECTION", "grievances")]
        
        complaints = list(collection.find({}, {"embedding": 0}))  # exclude embedding field
        for c in complaints:
            c["_id"] = str(c["_id"])  # convert ObjectId to string
        
        return complaints
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {e}")
    
@app.delete("/admin/complaints/{complaint_id}")
async def delete_complaint(complaint_id: str, current_user: str = Depends(get_current_user)):
    if current_user not in ["BHAVY", "SMARTYY"]:
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    try:
        from pymongo import MongoClient
        from bson import ObjectId
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        db = client[os.getenv("MONGO_DB", "hack")]
        collection = db[os.getenv("MONGO_COLLECTION", "grievances")]
        result = collection.delete_one({"_id": ObjectId(complaint_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    