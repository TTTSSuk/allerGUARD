import subprocess
import re
# import json

def analyze_each_allergen(normalized_ingredients, matching_allergens):
    """
    ให้ AI วิเคราะห์แต่ละสารที่ user แพ้อย่างละเอียด
    
    Args:
        normalized_ingredients: รายการส่วนผสมทั้งหมด (เรียงตามความเข้มข้น)
        matching_allergens: รายการสารที่ตรวจพบว่า user แพ้
            [{"allergen": "ชื่อที่ user พิมพ์", "ingredient": "ชื่อจริง", ...}]
    
    Returns:
        dict: {
            "status": "success/error",
            "raw_output": "คำแนะนำจาก AI (ภาษาไทย)",
            "analyzed_allergens": [
                {
                    "ingredient": "ชื่อสาร",
                    
                    "symptoms": "อาการที่อาจเกิด",
                    "recommendation": "คำแนะนำ",
                    "alternatives": ["สารทางเลือก1", "สารทางเลือก2"]
                }
            ]
        }
    """
    # "risk_level": "สูงมาก/สูง/ปานกลาง/ต่ำ",
    if not matching_allergens:
        return {
            "status": "success",
            "raw_output": "",
            "analyzed_allergens": []
        }
    
    # หาตำแหน่งของแต่ละสารในสูตร
    allergen_details = []
    for match in matching_allergens:
        ing_name = match["ingredient"]

        allergen_details.append({
            "ingredient": ing_name,
            "user_input": match.get("allergen", ing_name)
        })
        
        # หาตำแหน่งในสูตร
        # try:
            # position = normalized_ingredients.index(ing_name) + 1
            # total = len(normalized_ingredients)
            
            # # คำนวณความเข้มข้น
            # if position <= total * 0.2:
            #     concentration = "สูงมาก"
            # elif position <= total * 0.4:
            #     concentration = "สูง"
            # elif position <= total * 0.6:
            #     concentration = "ปานกลาง"
            # elif position <= total * 0.8:
            #     concentration = "ต่ำ"
            # else:
            #     concentration = "ต่ำมาก"
            
            # allergen_details.append({
            #     "ingredient": ing_name,
            #     "position": position,
            #     "total": total,
            #     "concentration": concentration,
            #     "user_input": match["allergen"]
            # })
            
        # except ValueError:
        #     allergen_details.append({
        #         "ingredient": ing_name,
        #         "position": "?",
        #         "total": len(normalized_ingredients),
        #         "concentration": "ไม่ทราบ",
        #         "user_input": match["allergen"]
        #     })
    
    # สร้าง Prompt สำหรับ AI
    prompt = create_analysis_prompt(allergen_details, normalized_ingredients)
    
    print("⏳ กำลังรอ AI วิเคราะห์...")
    
    try:
        result = subprocess.run(
            ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
            input=prompt,
            text=True,
            capture_output=True,
            encoding="utf-8",
            timeout=1500  # 5 นาที
        )
        
        ai_output = result.stdout.strip()
        
        print("✅ AI ตอบกลับมาแล้ว")
        print(ai_output)  # เพิ่มบรรทัดนี้
        
        # Parse AI output
        analyzed = parse_ai_output(ai_output, allergen_details)
        
        return {
            "status": "success",
            "raw_output": ai_output,
            "analyzed_allergens": analyzed
        }
        
    except subprocess.TimeoutExpired:
        print("❌ AI Timeout")
        return {
            "status": "error",
            "raw_output": "AI ตอบช้าเกินไป กรุณาลองใหม่อีกครั้ง",
            "analyzed_allergens": create_fallback_analysis(allergen_details)
        }
        
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return {
            "status": "error",
            "raw_output": f"เกิดข้อผิดพลาด: {str(e)}",
            "analyzed_allergens": create_fallback_analysis(allergen_details)
        }


def create_analysis_prompt(allergen_details, all_ingredients):
    
    ingredients_list = "\n".join([
        f"{i+1}. {ing}" 
        for i, ing in enumerate(all_ingredients)
    ])
    
    # แก้ตรงนี้ — ระบุให้ชัดว่าวิเคราะห์เฉพาะสารที่ระบุเท่านั้น
    detected_list = "\n".join([
        f"- {item['ingredient']} (ผู้ใช้แพ้สารนี้โดยตรง)"
        for item in allergen_details
    ])

    prompt = f"""คุณเป็นผู้เชี่ยวชาญด้านผิวหนังและเครื่องสำอาง

⚠️ สารที่ผู้ใช้แพ้และพบในผลิตภัณฑ์นี้:
{detected_list}

งานของคุณ: วิเคราะห์เฉพาะสารที่ระบุข้างบนเท่านั้น

สำหรับแต่ละสาร ให้ตอบในรูปแบบนี้:

---
[ชื่อสาร]
1. คำอธิบาย:
[อธิบายว่าสารนี้คืออะไร และทำไมคนที่แพ้ถึงควรระวัง]

2. สารทางเลือกที่ปลอดภัยกว่า:
   - [สาร 1] - [คุณสมบัติ]
   - [สาร 2] - [คุณสมบัติ]
---

กฎสำคัญ:
- ตอบเป็นภาษาไทยทั้งหมด
- วิเคราะห์เฉพาะสารที่ระบุเท่านั้น ห้ามข้าม
- คำอธิบายต้องเฉพาะเจาะจงกับสารนั้นๆ ห้ามใช้คำอธิบายเดิมซ้ำกัน
- ใช้ภาษาที่เข้าใจง่าย

เริ่มวิเคราะห์:"""
    
    return prompt

def parse_ai_output(ai_output, allergen_details):
    analyzed = []
    sections = re.split(r'\n---+\n', ai_output)
    
    for section in sections:
        if not section.strip():
            continue
        
        name_match = re.search(r'^\s*([A-Z][A-Z\s\-\/\(\)0-9]+)', section, re.MULTILINE)
        if not name_match:
            continue
        
        ingredient_name = name_match.group(1).strip()
        
        # ดึงคำอธิบาย
        desc_match = re.search(r'คำอธิบาย:\s*(.*?)(?=\d+\.|---|\Z)', section, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else "ไม่ทราบ"
        
        # ดึงสารทางเลือก
        alt_section = re.search(r'สารทางเลือก.*?:(.*?)(?=---|\Z)', section, re.DOTALL)
        alternatives = []
        if alt_section:
            alternatives = [
                s.strip().lstrip('- ') 
                for s in alt_section.group(1).split('\n') 
                if s.strip().startswith('-')
            ]
        
        analyzed.append({
            "ingredient": ingredient_name,
            "description": description,   # เปลี่ยนจาก symptoms
            "alternatives": alternatives
        })
    
    if not analyzed:
        print("⚠️ Parse AI output ไม่สำเร็จ ใช้ fallback")
        analyzed = create_fallback_analysis(allergen_details)
    
    return analyzed


def create_fallback_analysis(allergen_details):
    fallback = []
    for item in allergen_details:
        fallback.append({
            "ingredient": item["ingredient"],
            "description": "ไม่สามารถวิเคราะห์ได้ ควรปรึกษาแพทย์ผิวหนัง",
            "alternatives": ["ปรึกษาแพทย์เพื่อหาสารทางเลือก"]
        })
    return fallback


# ฟังก์ชันเก่าสำหรับ backward compatibility
def process_with_ai(normalized_ingredients, user_allergies, detected_allergens):
    """
    ฟังก์ชันเก่า (deprecated) - เก็บไว้เพื่อ compatibility
    แนะนำให้ใช้ analyze_each_allergen() แทน
    """
    print("⚠️ Warning: process_with_ai() is deprecated. Use analyze_each_allergen() instead.")
    
    # แปลง detected_allergens เป็น matching_allergens format
    matching_allergens = [
        {
            "allergen": d.get("matched_allergen", d.get("ingredient", "")),
            "ingredient": d.get("ingredient", ""),
            "match_score": 1.0,
            "reason": "เก่า format"
        }
        for d in detected_allergens
    ]
    
    return analyze_each_allergen(normalized_ingredients, matching_allergens)