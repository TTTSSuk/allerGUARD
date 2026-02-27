from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import json
import os
from pipeline import run_pipeline

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# สร้าง static folder ถ้ายังไม่มี
if not os.path.exists("static"):
    os.makedirs("static")
    print("✅ สร้าง static folder แล้ว")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"⚠️ Warning: {e}")

# หน้าแรก - ส่ง index.html
@app.get("/", response_class=HTMLResponse)
async def read_index():
    """แสดงหน้าเว็บหลัก"""
    print("📄 กำลังโหลดหน้า index.html")
    
    # ลองหาไฟล์ index.html ใน static หรือ current directory
    possible_paths = [
        "static/index.html",
        "index.html",
        os.path.join(os.path.dirname(__file__), "static", "index.html"),
        os.path.join(os.path.dirname(__file__), "index.html")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    print(f"✅ โหลด index.html จาก {path}")
                    return content
            except Exception as e:
                print(f"⚠️ Error loading {path}: {e}")
                continue
    
    # ถ้าไม่เจอ ให้แสดง error
    print("❌ ไม่พบไฟล์ index.html")
    return """
    <html>
    <head>
        <title>AllerGUARD - Setup Required</title>
        <style>
            body { font-family: Arial; padding: 40px; background: #1a1a1a; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #7c3aed; }
            .code { background: #2a2a2a; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚙️ AllerGUARD - Setup Required</h1>
            <p>ไม่พบไฟล์ <strong>index.html</strong></p>
            <p>กรุณาวางไฟล์ <code>index.html</code> ใน folder <code>static/</code></p>
            
            <h3>วิธีแก้ไข:</h3>
            <div class="code">
                <pre>mkdir static
mv index.html static/</pre>
            </div>
            
            <p>หรือ</p>
            
            <div class="code">
                <pre>python app.py</pre>
            </div>
            
            <p>ไฟล์ที่ค้นหา: {}</p>
        </div>
    </body>
    </html>
    """.format("<br>".join(possible_paths))


@app.post("/analyze-label")
async def analyze_label(file: UploadFile = File(...), allergies: str = Form("[]")):
    """
    Endpoint สำหรับวิเคราะห์ฉลากเครื่องสำอาง
    
    รับ:
        - file: ไฟล์ภาพฉลาก
        - allergies: JSON array ของสารที่แพ้
    
    ตอบกลับ:
        - ingredients: รายการส่วนผสมที่พบ
        - analysis: ผลการวิเคราะห์ความเสี่ยง
    """
    print("\n" + "="*70)
    print("🔵 เริ่มต้น analyze_label endpoint")
    print(f"📎 ไฟล์ที่อัปโหลด: {file.filename}")
    
    # บันทึกไฟล์ชั่วคราว
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"💾 บันทึกไฟล์ชั่วคราวที่: {temp_path}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return {
            "error": f"Failed to save file: {str(e)}",
            "ingredients": [],
            "analysis": {
                "risky_ingredients": [],
                "summary": "ไม่สามารถบันทึกไฟล์ได้"
            }
        }

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
        
        # แปลง format ให้ตรงกับที่ frontend ต้องการ
        response = convert_to_frontend_format(result)
        
        print(f"📊 Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ Error ใน pipeline: {e}")
        import traceback
        traceback.print_exc()
        
        response = {
            "error": str(e),
            "ingredients": [],
            "analysis": {
                "risky_ingredients": [],
                "summary": f"เกิดข้อผิดพลาด: {str(e)}"
            }
        }
    
    # ลบไฟล์ชั่วคราว
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"🗑️ ลบไฟล์ชั่วคราว: {temp_path}")
    except Exception as e:
        print(f"⚠️ ไม่สามารถลบไฟล์ชั่วคราว: {e}")
    
    print("="*70 + "\n")
    return response


def convert_to_frontend_format(pipeline_result):
    """
    แปลงผลลัพธ์จาก pipeline ให้ตรงกับ format ที่ frontend ต้องการ
    
    Pipeline format:
    {
        "status": "success",
        "cleaned_ingredients": [...],
        "detected_allergens": [...],
        "recommendation": "...",
        "ai_analysis": "..."
    }
    
    Frontend format:
    {
        "ingredients": [{original, corrected}, ...],
        "analysis": {
            "risky_ingredients": [{name, risk_level, reason, ...}, ...],
            "summary": "..."
        }
    }
    """
    
    # สร้าง ingredients list
    ingredients = []
    for ing in pipeline_result.get("cleaned_ingredients", []):
        ingredients.append({
            "original": ing,
            "corrected": ing,
            "confidence": "สูง"
        })
    
    # สร้าง risky_ingredients list
    risky_ingredients = []
    for allergen in pipeline_result.get("detected_allergens", []):
        risky_ingredients.append({
            "name": allergen.get("ingredient", "Unknown"),
            "name_th": allergen.get("matched_allergen", ""),
            "risk_level": map_risk_level(allergen.get("risk_level", "ต่ำ")),
            "reason": f"{allergen.get('match_reason', '')} - {allergen.get('symptoms', '')}",
            "precaution": allergen.get("recommendation", "ควรระวัง")
        })
    
    # สร้าง summary
    summary = pipeline_result.get("recommendation", "")
    if pipeline_result.get("ai_analysis"):
        summary += "\n\n" + pipeline_result["ai_analysis"]
    
    return {
        "ingredients": ingredients,
        "analysis": {
            "risky_ingredients": risky_ingredients,
            "summary": summary.strip()
        }
    }


def map_risk_level(thai_risk_level):
    """แปลงระดับความเสี่ยงจากไทยเป็นอังกฤษ"""
    mapping = {
        "สูงมาก": "สูง",
        "สูง": "สูง",
        "ปานกลาง": "กลาง",
        "ต่ำ": "ต่ำ",
        "ต่ำมาก": "ต่ำ",
        "high": "สูง",
        "medium": "กลาง",
        "low": "ต่ำ"
    }
    
    level = thai_risk_level.lower()
    for key, value in mapping.items():
        if key in level:
            return value
    
    return "ต่ำ"


@app.get("/health")
async def health_check():
    """ตรวจสอบสถานะของระบบ"""
    return {
        "status": "ok",
        "message": "AllerGUARD API is running",
        "version": "2.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 AllerGUARD - AI Ingredient Scanner")
    print("="*70)
    print("📍 URL: http://127.0.0.1:8000")
    print("📝 API Docs: http://127.0.0.1:8000/docs")
    print("💚 Health Check: http://127.0.0.1:8000/health")
    print("="*70 + "\n")
    
    # เช็คว่ามี index.html หรือยัง
    if not os.path.exists("static/index.html") and not os.path.exists("index.html"):
        print("⚠️ WARNING: ไม่พบไฟล์ index.html")
        print("   กรุณาวางไฟล์ index.html ใน folder static/\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",  # เปิดให้เข้าถึงจากภายนอกได้
        port=8000,
        reload=True
    )