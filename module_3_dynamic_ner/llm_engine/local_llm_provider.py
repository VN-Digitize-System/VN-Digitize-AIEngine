import json
import time
import re
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from llm_engine.llm_provider import BaseLLMProvider

class LocalLLMProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(api_key="ollama")
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama" 
        )
        self.primary_model = "qwen2.5:7b"
        
        self.max_chars_per_chunk = 8000
        self.overlap_chars = 500
        self.processing_mode = os.getenv("CHUNK_PROCESSING_MODE", "sequential").lower()
        
        # Đảm bảo thư mục logs tồn tại
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.trace_file = os.path.join(self.log_dir, "m3_llm_trace.log")

    def _log_trace(self, chunk_index: int, total_chunks: int, prompt: str, raw_response: str, latency: float, error: str = None):
        """Ghi vết LLM dưới định dạng Văn bản thuần (Human-Readable)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if not error else f"ERROR: {error}"
        
        trace_content = f"""
{'='*80}
[TIMESTAMP]: {timestamp} | [CHUNK]: {chunk_index}/{total_chunks} | [LATENCY]: {latency:.2f}s | [STATUS]: {status}
{'-'*80}
[FULL PROMPT SENT TO LLM]:
{prompt.strip()}
{'-'*80}
[RAW RESPONSE FROM LLM]:
{raw_response.strip() if raw_response else 'No Response'}
{'='*80}
"""
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(trace_content)

    def _semantic_chunking(self, text: str) -> list[str]:
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.max_chars_per_chunk:
                current_chunk += para + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                overlap_start = max(0, len(current_chunk) - self.overlap_chars)
                current_chunk = current_chunk[overlap_start:] + para + "\n\n"
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text]

    def _process_single_chunk(self, chunk: str, json_schema: dict, system_prompt: str, chunk_index: int, total_chunks: int) -> dict:
        prompt = f"""
        {system_prompt}
        
        Quy tắc bắt buộc: Không giải thích, chỉ trả về JSON. Trích xuất thông tin CÓ TRONG đoạn dưới đây:

        [VĂN BẢN (Phần {chunk_index}/{total_chunks})]:
        {chunk}

        [CẤU TRÚC JSON]:
        {json.dumps(json_schema, ensure_ascii=False, indent=2)}
        """
        
        start_time = time.time()
        raw_response = ""
        error_msg = None
        
        try:
            print(f"⏳ [Local LLM] Đang xử lý khối {chunk_index}/{total_chunks} (Timeout: 120s)...")
            response = self.client.chat.completions.create(
                model=self.primary_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                timeout=120.0
            )
            
            raw_response = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            
            latency = time.time() - start_time
            self._log_trace(chunk_index, total_chunks, prompt, raw_response, latency)
            
            if json_match:
                return json.loads(json_match.group(0))
            else:
                print(f"⚠️ [Lỗi Parsing] Khối {chunk_index} không sinh ra JSON hợp lệ.")
                return {}
                
        except Exception as e:
            latency = time.time() - start_time
            error_msg = str(e)
            self._log_trace(chunk_index, total_chunks, prompt, raw_response, latency, error=error_msg)
            print(f"❌ [CRASH/TIMEOUT] Khối {chunk_index} thất bại: {error_msg}")
            return {}

    def extract_batch_json(self, context_text: str, json_schema: dict, system_prompt: str) -> dict:
        chunks = self._semantic_chunking(context_text)
        print(f"📦 [Chunking] Tài liệu được chia thành {len(chunks)} khối ngữ nghĩa.")
        
        final_extracted_data = {}
        chunk_results = []

        if self.processing_mode == "parallel" and len(chunks) > 1:
            print("🚀 [Local LLM] Chế độ SONG SONG: Bật đa luồng (Multi-threading)...")
            with ThreadPoolExecutor(max_workers=min(len(chunks), 5)) as executor:
                futures = [executor.submit(self._process_single_chunk, chunk, json_schema, system_prompt, i+1, len(chunks)) for i, chunk in enumerate(chunks)]
                for future in as_completed(futures):
                    chunk_results.append(future.result())
        else:
            print("🐢 [Local LLM] Chế độ TUẦN TỰ: Xử lý an toàn từng khối một...")
            for i, chunk in enumerate(chunks):
                result = self._process_single_chunk(chunk, json_schema, system_prompt, i+1, len(chunks))
                chunk_results.append(result)

        for chunk_data in chunk_results:
            for key, value in chunk_data.items():
                if value and str(value).lower() not in ["null", "none", ""]:
                    if key not in final_extracted_data or not final_extracted_data[key]:
                        final_extracted_data[key] = value

        print("✅ [Local LLM] Hoàn tất bóc tách và gộp dữ liệu!")
        return final_extracted_data