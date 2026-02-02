import subprocess

def analyze_with_ai(ocr_text, user_allergies):
    prompt = f"""
คุณเป็นผู้เชี่ยวชาญด้านส่วนผสมในเครื่องสำอางและการแพ้สารเคมี

ข้อมูลฉลากสินค้า:
{ocr_text}

สิ่งที่ผู้ใช้แพ้:
{", ".join(user_allergies)}

งานของคุณ:
1. ระบุส่วนผสมที่พบ
2. วิเคราะห์ว่าส่วนผสมใดเกี่ยวข้องกับสิ่งที่ผู้ใช้แพ้
3. อธิบายเหตุผล
4. ประเมินระดับความเสี่ยง (ต่ำ / ปานกลาง / สูง)

ตอบกลับเป็นโครงสร้างนี้เท่านั้น:

Ingredients Detected:
- ...

Risky Ingredients:
- Name:
  Reason:
  Risk Level:

Overall Summary:
- ...
"""

    result = subprocess.run(
        [
            "ollama",
            "run",
            "scb10x/llama3.1-typhoon2-8b-instruct"
        ],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )

    return result.stdout


if __name__ == "__main__":
    # 🔹 ตัวอย่างข้อมูล (ของจริงจะมาจาก OCR)
    ocr_text = """
    Ingredients: Water, Salicylic Acid, Glycerin, Phenoxyethanol
    """

    user_allergies = ["Salicylate"]

    ai_result = analyze_with_ai(ocr_text, user_allergies)

    print("===== AI ANALYSIS RESULT =====")
    print(ai_result)
