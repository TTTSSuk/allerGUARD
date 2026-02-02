from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import shutil
import json
import os
from pipeline import run_pipeline

app = FastAPI()

# ให้ Backend เรียกใช้ไฟล์ในโฟลเดอร์ static ได้
if not os.path.exists("static"):
    os.makedirs("static")

# หน้าแรกให้โชว์ index.html
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/analyze-label")
async def analyze_label(file: UploadFile = File(...), allergies: str = Form("[]")):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    allergy_list = json.loads(allergies) #
    
    # รัน pipeline ที่เชื่อมกับ Gemini AI
    result = run_pipeline(temp_path, allergy_list)
    
    # ลบไฟล์ชั่วคราวหลังใช้เสร็จ
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return result

if __name__ == "__main__":
    import uvicorn
    import sys
    import subprocess
    
    # ใช้ subprocess เพื่อให้ reload ทำงานได้
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8000"
    ])