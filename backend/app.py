from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import shutil
import json
import os
from pipeline import run_pipeline

app = FastAPI()

# สร้าง static folder ถ้ายังไม่มี
if not os.path.exists("static"):
    os.makedirs("static")
    print("✅ สร้าง static folder แล้ว")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# หน้าแรก
@app.get("/", response_class=HTMLResponse)
async def read_index():
    print("📄 กำลังโหลดหน้า index.html")
    try:
        with open("static/index.html", encoding="utf-8") as f:
            content = f.read()
            print("✅ โหลด index.html สำเร็จ")
            return content
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ static/index.html")
        return """
        <h1>❌ ไม่พบไฟล์ index.html</h1>
        <p>กรุณาวางไฟล์ index.html ใน folder static/</p>
        """

@app.post("/analyze-label")
async def analyze_label(file: UploadFile = File(...), allergies: str = Form("[]")):
    print("\n" + "="*50)
    print("🔵 เริ่มต้น analyze_label endpoint")
    print(f"📎 ไฟล์ที่อัปโหลด: {file.filename}")
    
    # บันทึกไฟล์ชั่วคราว
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"💾 บันทึกไฟล์ชั่วคราวที่: {temp_path}")

    # Parse allergies
    try:
        allergy_list = json.loads(allergies)
        print(f"🔴 สารที่แพ้: {allergy_list}")
    except Exception as e:
        print(f"⚠️ Error parsing allergies: {e}")
        allergy_list = []
    
    # เรียก AI pipeline
    print("🤖 เริ่มเรียก AI pipeline...")
    try:
        result = run_pipeline(temp_path, allergy_list)
        print("✅ Pipeline เสร็จสมบูรณ์")
        print(f"📊 ผลลัพธ์: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Error ใน pipeline: {e}")
        import traceback
        traceback.print_exc()
        result = {"error": str(e)}
    
    # ลบไฟล์ชั่วคราว
    if os.path.exists(temp_path):
        os.remove(temp_path)
        print(f"🗑️ ลบไฟล์ชั่วคราว: {temp_path}")
    
    print("="*50 + "\n")
    return result

if __name__ == "__main__":
    import uvicorn
    print("🚀 กำลังเริ่ม FastAPI server...")
    print("📍 URL: http://127.0.0.1:8000")
    print("📝 Swagger Docs: http://127.0.0.1:8000/docs")
    print("-" * 50)
    
    uvicorn.run(
        "app:app",
        reload=True,
        host="127.0.0.1",
        port=8000
    )