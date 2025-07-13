# backend/app/routes.py
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.analyzer import analyze_chat

router = APIRouter()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        result = analyze_chat(contents.decode("utf-8"))
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
