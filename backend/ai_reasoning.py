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
    
    detected_list = "\n".join([
        f"- {item['ingredient']}"
        for item in allergen_details
    ])

    prompt = f"""คุณเป็นผู้เชี่ยวชาญด้านผิวหนังและเครื่องสำอาง

ส่วนผสมทั้งหมดในผลิตภัณฑ์ (เรียงตามความเข้มข้น จากมากไปน้อย):
{ingredients_list}

ผู้ใช้แพ้สารเหล่านี้ที่พบในผลิตภัณฑ์:
{detected_list}

งานของคุณ: วิเคราะห์แต่ละสารที่ผู้ใช้แพ้อย่างละเอียด

สำหรับแต่ละสาร ให้ตอบในรูปแบบนี้:

---
[ชื่อสาร]
1. อาการที่อาจเกิดขึ้น:
   - [อาการ 1]
   - [อาการ 2]
   - [อาการ 3]

2. คำอธิบาย:
[อธิบายลักษณะของสารและเหตุผลที่ผู้ที่แพ้ควรระวัง]

3. คำแนะนำ:
   [ไม่ควรใช้/ห้ามใช้]

4. สารทางเลือกที่ปลอดภัยกว่า:
   - [สาร 1] - [คุณสมบัติ]
   - [สาร 2] - [คุณสมบัติ]
---

กฎสำคัญ:
- ตอบเป็นภาษาไทยทั้งหมด
- วิเคราะห์ทุกสารที่ระบุมา ห้ามข้าม
- ใช้ภาษาที่เข้าใจง่าย

เริ่มวิเคราะห์:"""
    
    return prompt


def parse_ai_output(ai_output, allergen_details):
    """แปลง AI output เป็น structured data"""
    
    analyzed = []
    
    # แยกแต่ละสาร (คั่นด้วย ---)
    sections = re.split(r'\n---+\n', ai_output)
    
    for section in sections:
        if not section.strip():
            continue
        
        # ดึงชื่อสาร
        # name_match = re.search(r'🔴\s+([A-Z\s\(\)\-\/]+?)\s+\(', section)
        name_match = re.search(r'^\s*([A-Z][A-Z\s\-\/\(\)]+)', section, re.MULTILINE)
        if not name_match:
            continue
        
        ingredient_name = name_match.group(1).strip()
        
        # ดึงระดับความเสี่ยง
        # risk_match = re.search(r'ระดับความเสี่ยง:\s*(.+)', section)
        # risk_level = risk_match.group(1).strip() if risk_match else "ไม่ทราบ"
        
        # ดึงอาการ
        symptoms_section = re.search(r'อาการที่อาจเกิดขึ้น:(.*?)(?=\d+\.|---|\Z)', section, re.DOTALL)
        symptoms = []
        if symptoms_section:
            symptoms_text = symptoms_section.group(1)
            symptoms = [
                s.strip().lstrip('- ') 
                for s in symptoms_text.split('\n') 
                if s.strip().startswith('-')
            ]
        
        # ดึงคำแนะนำ
        rec_match = re.search(r'คำแนะนำ:\s*(.+)', section)
        recommendation = rec_match.group(1).strip() if rec_match else "ควรระวัง"
        
        # ดึงสารทางเลือก
        alt_section = re.search(r'สารทางเลือก.*?:(.*?)(?=---|\Z)', section, re.DOTALL)
        alternatives = []
        if alt_section:
            alt_text = alt_section.group(1)
            alternatives = [
                s.strip().lstrip('- ') 
                for s in alt_text.split('\n') 
                if s.strip().startswith('-')
            ]
        
        analyzed.append({
            "ingredient": ingredient_name,
            # "risk_level": risk_level,
            "symptoms": ", ".join(symptoms) if symptoms else "ไม่ทราบ",
            "recommendation": recommendation,
            "alternatives": alternatives
        })
    
    # ถ้า parse ไม่ได้ ให้ fallback
    if not analyzed:
        print("⚠️ Parse AI output ไม่สำเร็จ ใช้ fallback")
        analyzed = create_fallback_analysis(allergen_details)
    
    return analyzed


def create_fallback_analysis(allergen_details):
    """สร้างข้อมูลสำรองถ้า AI ล้มเหลว"""
    
    fallback = []
    
    for item in allergen_details:
        # risk_map = {
        #     "สูงมาก": "สูงมาก - ควรหลีกเลี่ยง",
        #     "สูง": "สูง - ไม่ควรใช้",
        #     "ปานกลาง": "ปานกลาง - ใช้ด้วยความระวัง",
        #     "ต่ำ": "ต่ำ - ควรระวัง",
        #     "ต่ำมาก": "ต่ำมาก - อาจใช้ได้",
        #     "ไม่ทราบ": "ต้องตรวจสอบ"
        # }
        
        fallback.append({
            "ingredient": item["ingredient"],
            # "risk_level": risk_map.get(item["concentration"], "ต้องตรวจสอบ"),
            "symptoms": "อาจเกิดอาการแพ้ เช่น แดง คัน ผื่น บวม",
            "recommendation": "ควรปรึกษาแพทย์ผิวหนังก่อนใช้",
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