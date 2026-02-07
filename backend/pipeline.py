from ocr_tess_test import ocr_image
from ingredient_extractor import extract_ingredients
from ai_normalize import normalize_ingredients
from ai_reasoning import process_with_ai

def run_pipeline(image_path, user_allergies=None):
    if user_allergies is None:
        user_allergies = []
    
    print("🔵 เริ่มต้น pipeline...")

    # 1. OCR + Extract
    raw_text = ocr_image(image_path)
    ingredients = extract_ingredients(raw_text)
    
    if not ingredients:
        return {
            "status": "error",
            "cleaned_ingredients": [],
            "detected_allergens": [],
            "recommendation": "ไม่พบส่วนผสมในฉลาก",
            "ai_analysis": ""
        }

    # 2. Normalize (ข้ามถ้าช้า)
    print("🔄 กำลัง normalize ชื่อสาร...")
    try:
        normalized_results = normalize_ingredients(ingredients)
        normalized_ingredients = [
            item["corrected"].upper()
            for item in normalized_results
            if item["corrected"] != "uncertain"
        ]
    except Exception as e:
        print(f"⚠️ Normalize ล้มเหลว: {e}")
        # ใช้ชื่อดิบแทน
        normalized_ingredients = [ing.upper() for ing in ingredients]
    
    print(f"✅ พบ {len(normalized_ingredients)} รายการ")

    # 3. ตรวจ allergen แบบ substring (เร็ว)
    detected_substring = []
    user_allergies_upper = [u.upper() for u in user_allergies]

    for ing in normalized_ingredients:
        for allergy in user_allergies_upper:
            if allergy in ing:
                detected_substring.append({
                    "ingredient": ing,
                    "reason": f"พบคำว่า '{allergy}' ในชื่อสาร",
                    "level": "HIGH",
                    "source": "substring"
                })
                break  # เจอแล้วไม่ต้องเช็คต่อ

    # 4. AI Analysis (หาสารในกลุ่มเดียวกัน)
    ai_detected = []
    ai_output = ""
    
    if user_allergies:
        try:
            print("🤖 กำลังให้ AI วิเคราะห์...")
            ai_result = process_with_ai(normalized_ingredients, user_allergies)
            
            if ai_result["status"] == "success":
                ai_detected = ai_result.get("detected_allergens", [])
                ai_output = ai_result.get("raw_ai_output", "")
                
                # เพิ่ม source tag
                for item in ai_detected:
                    item["source"] = "ai"
        
        except Exception as e:
            print(f"⚠️ AI Error: {e}")
            ai_output = f"AI วิเคราะห์ไม่สำเร็จ: {str(e)}"

    # 5. รวมผลลัพธ์ (ไม่ซ้ำ)
    all_detected = detected_substring.copy()
    
    # เพิ่มที่ AI เจอแต่ substring ไม่เจอ
    substring_ings = {d["ingredient"] for d in detected_substring}
    for ai_item in ai_detected:
        if ai_item["ingredient"] not in substring_ings:
            all_detected.append(ai_item)
    
    # 6. สรุปผล
    recommendation = ""
    if all_detected:
        high_risk = [d for d in all_detected if d.get("level", "").upper() == "HIGH"]
        if high_risk:
            recommendation = f"⚠️ พบสารที่แพ้ {len(high_risk)} รายการ - ควรหลีกเลี่ยง"
        else:
            recommendation = f"⚡ พบสารที่อาจแพ้ {len(all_detected)} รายการ - ควรระวัง"
    else:
        recommendation = "✅ ปลอดภัยสำหรับคุณ"

    return {
        "status": "success",
        "cleaned_ingredients": normalized_ingredients,
        "detected_allergens": all_detected,
        "recommendation": recommendation,
        "ai_analysis": ai_output
    }