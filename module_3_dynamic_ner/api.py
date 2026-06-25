import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from schemas.template_schema import DocumentInput
from pipeline import DocumentPipeline
from router.classifier import UnknownDocumentError

# Nạp biến môi trường
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Chưa cấu hình GEMINI_API_KEY trong file .env")

# Khởi tạo Pipeline (Bỏ lệnh đọc file cứng)
pipeline = DocumentPipeline(api_key=api_key)

app = FastAPI(title="Document AI API", description="API Trích xuất dữ liệu Hybrid")

class ExtractionOptions(BaseModel):
    enable_auto_correct: bool = False

class ExtractionRequest(BaseModel):
    document: DocumentInput
    options: ExtractionOptions = ExtractionOptions()

@app.post("/api/v1/extract")
async def extract_document(request: ExtractionRequest):
    start_time = time.time()
    
    try:
        # Pipeline tự động phân loại và nạp cấu hình
        results = pipeline.process(
            document=request.document, 
            enable_auto_correct=request.options.enable_auto_correct
        )
        
        process_time = round(time.time() - start_time, 2)
        
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
        
    # --- BẮT LỖI TÀI LIỆU RÁC (HTTP 400) ---
    except UnknownDocumentError as e:
        raise HTTPException(status_code=400, detail={"status": "error", "message": str(e)})
        
    # --- BẮT LỖI HỆ THỐNG / CẤU HÌNH (HTTP 500) ---
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})
        
    # Lỗi không xác định
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})