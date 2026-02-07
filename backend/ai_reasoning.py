import subprocess
import json

def analyze_ingredients(normalized_ingredients, user_allergies):
    prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านการวิเคราะห์สารก่อภูมิแพ้ในเครื่องสำอาง

ส่วนผสมที่ตรวจพบ (JSON):
{json.dumps(normalized_ingredients, ensure_ascii=False)}

สารที่ผู้ใช้แพ้:
{", ".join(user_allergies)}

งานของคุณ:
1. ระบุสารที่อาจก่อให้เกิดอาการแพ้
2. อธิบายเหตุผลเป็นภาษาไทยอย่างละเอียด
3. ระบุระดับความเสี่ยง (ต่ำ/กลาง/สูง)
4. แนะนำข้อควรระวัง

กฎการตอบ:
- ตอบเป็นภาษาไทยทั้งหมด
- อธิบายให้เข้าใจง่าย
- ระบุชื่อสารเป็นภาษาอังกฤษ แต่อธิบายเป็นภาษาไทย
- ถ้าไม่มีสารที่เสี่ยง ให้ risky_ingredients เป็น array ว่าง

ตอบเป็น JSON เท่านั้น:
{{
  "risky_ingredients": [
    {{
      "name": "ชื่อสารภาษาอังกฤษ",
      "name_th": "ชื่อสารภาษาไทย (ถ้ามี)",
      "reason": "อธิบายว่าทำไมถึงเสี่ยง เช่น เป็นสาร salicylate ที่คุณแพ้ อาจทำให้เกิดผื่นแดง คัน หรือระคายเคือง",
      "risk_level": "สูง | กลาง | ต่ำ",
      "precaution": "ข้อควรระวังเพิ่มเติม เช่น หลีกเลี่ยงการใช้บริเวณผิวที่บอบบาง"
    }}
  ],
  "summary": "สรุปผลการวิเคราะห์เป็นภาษาไทย เช่น พบสาร 2 ชนิดที่อาจทำให้คุณแพ้ ควรหลีกเลี่ยงการใช้ผลิตภัณฑ์นี้",
  "safe_to_use": true หรือ false
}}
"""

    result = subprocess.run(
        ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )

    output = result.stdout.strip()
    output = output[:output.rfind("}")+1]

    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing AI response: {e}")
        print(f"Raw output: {output}")
        return {
            "risky_ingredients": [],
            "summary": "เกิดข้อผิดพลาดในการวิเคราะห์ กรุณาลองใหม่อีกครั้ง",
            "safe_to_use": None
        }