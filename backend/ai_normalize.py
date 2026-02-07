import subprocess
import json

def normalize_ingredients(ingredient_list):
    # ถ้ามีสารเยอะมาก (>20) ให้ข้ามเพื่อความเร็ว
    if len(ingredient_list) > 50:
        print("⚠️ สารมีจำนวนมาก - ข้าม normalize")
        return [
            {
                "original": ing,
                "corrected": ing,
                "confidence": "ต่ำ"
            }
            for ing in ingredient_list
        ]
    
    ingredients_text = "\n".join(ingredient_list)

    prompt = f"""
คุณเป็นเครื่องมือแก้ไขชื่อสารในเครื่องสำอาง

Input คือรายการชื่อสารที่อ่านจาก OCR (อาจมีความผิดพลาด)
แต่ละบรรทัดคือ 1 สาร

รายการสารจาก OCR:
{ingredients_text}

กฎการทำงาน:
- ประมวลผลทีละ 1 บรรทัด
- แก้ไขชื่อสารให้ถูกต้อง (ใช้ชื่อวิทยาศาสตร์ภาษาอังกฤษ)
- ถ้าไม่แน่ใจ ให้ corrected = "uncertain"
- ระบุความมั่นใจ: สูง/กลาง/ต่ำ
- Output ต้องมีจำนวนเท่ากับ Input
- ตอบเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบาย

ตัวอย่าง:
Input: "Salicylic 0id"
Output: {{"original": "Salicylic 0id", "corrected": "Salicylic Acid", "confidence": "สูง"}}

ตอบเป็น JSON Array เท่านั้น:
[
  {{
    "original": "ชื่อเดิม",
    "corrected": "ชื่อที่แก้แล้ว",
    "confidence": "สูง | กลาง | ต่ำ"
  }}
]
"""

    print("⏳ รอ AI normalize... )")
    
    try:
        result = subprocess.run(
            ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
            input=prompt,
            text=True,
            capture_output=True,
            encoding="utf-8",
            timeout=1800  # เพิ่ม timeout 60 วินาที
        )

        output = result.stdout.strip()
        
        # หา JSON array จากผลลัพธ์
        try:
            parsed = json.loads(output)
            print("✅ Normalize สำเร็จ")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ AI ตอบไม่เป็น JSON: {e}")
            print("Raw:", output[:200])
            raise  # ส่ง error ต่อไป
            
    except subprocess.TimeoutExpired:
        print("❌ AI Normalize timeout")
        raise
    except Exception as e:
        print(f"❌ Normalize error: {e}")
        # Fallback: คืนค่าเดิม
        return [
            {
                "original": ing,
                "corrected": ing,
                "confidence": "ต่ำ"
            }
            for ing in ingredient_list
        ]