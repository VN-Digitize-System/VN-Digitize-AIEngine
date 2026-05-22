import os
import json
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from schemas.template_schema import DocumentInput
from pipeline import DocumentPipeline

# Nạp biến môi trường và khởi tạo Pipeline
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Chưa cấu hình GEMINI_API_KEY trong file .env")

pipeline = DocumentPipeline(api_key=api_key)

# Đọc luật từ JSON một lần khi khởi động server
with open("configs/rules_hanh_chinh.json", "r", encoding="utf-8") as f:
    RULES_CONFIG = json.load(f).get("fields", {})

app = FastAPI(title="Document AI API", description="API Trích xuất dữ liệu Hybrid")

# Cấu hình request từ Frontend
class ExtractionOptions(BaseModel):
    enable_auto_correct: bool = False

class ExtractionRequest(BaseModel):
    document: DocumentInput
    options: ExtractionOptions = ExtractionOptions()

@app.post("/api/v1/extract")
async def extract_document(request: ExtractionRequest):
    start_time = time.time()
    
    try:
        # Đưa dữ liệu vào Pipeline
        results = pipeline.process(
            document=request.document, 
            rules_config=RULES_CONFIG,
            enable_auto_correct=request.options.enable_auto_correct
        )
        
        process_time = round(time.time() - start_time, 2)
        
        # Trả về chuẩn JSend (Option 2B)
        return {
            "status": "success",
            "data": {
                "extracted_fields": [field.dict() for field in results]
            },
            "metadata": {
                "processing_time_seconds": process_time,
                "auto_correct_applied": request.options.enable_auto_correct
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lệnh chạy server: uvicorn api:app --reload