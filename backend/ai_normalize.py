import subprocess
import json

def normalize_ingredients(ingredient_list):
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

    result = subprocess.run(
        ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )

    output = result.stdout.strip()
    
    # หา JSON array จากผลลัพธ์
    try:
        # หาตำแหน่ง [ และ ] สุดท้าย
        start = output.find("[")
        end = output.rfind("]") + 1
        
        if start != -1 and end > start:
            json_str = output[start:end]
            return json.loads(json_str)
        else:
            # ถ้าหาไม่เจอ ลองตัดทีหลัง
            output = output[:output.rfind("]")+1]
            return json.loads(output)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing normalize response: {e}")
        print(f"Raw output: {output}")
        
        # Fallback: คืนค่าเดิม
        return [
            {
                "original": ing,
                "corrected": ing,
                "confidence": "ต่ำ"
            }
            for ing in ingredient_list
        ]