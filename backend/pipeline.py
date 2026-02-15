from ocr_tess_test import ocr_image
from ingredient_extractor import extract_ingredients
from ai_normalize import normalize_ingredients
from ai_reasoning import analyze_each_allergen
from fuzzy_matcher import find_matching_allergens

def run_pipeline(image_path, user_allergies=None):
    """
    Pipeline หลักสำหรับตรวจสอบสารที่แพ้
    
    Workflow:
    1️⃣ OCR อ่านภาพ
    2️⃣ Normalize รายชื่อสาร (แก้ไข OCR errors)
    3️⃣ เปรียบเทียบกับสารที่ user แพ้ (ใช้ fuzzy matching)
    4️⃣ ส่งแต่ละสารที่แพ้ให้ AI วิเคราะห์ระดับความเสี่ยง + คำแนะนำ
    5️⃣ รวมผลลัพธ์และส่งกลับไปแสดงบนเว็บ
    """
    
    if user_allergies is None:
        user_allergies = []
    
    print("\n" + "="*70)
    print("🚀 เริ่มต้น AllerGUARD Pipeline")
    print("="*70)

    # =========================================================================
    # 1️⃣ OCR อ่านภาพ
    # =========================================================================
    print("\n📸 STEP 1: OCR อ่านภาพ...")
    try:
        raw_text = ocr_image(image_path)
        print(f"✅ OCR สำเร็จ (อ่านได้ {len(raw_text)} ตัวอักษร)")
    except Exception as e:
        print(f"❌ OCR ล้มเหลว: {e}")
        return {
            "status": "error",
            "message": f"ไม่สามารถอ่านภาพได้: {str(e)}",
            "cleaned_ingredients": [],
            "detected_allergens": [],
            "recommendation": "กรุณาลองใหม่อีกครั้ง",
            "ai_analysis": ""
        }
    
    # =========================================================================
    # 2️⃣ Normalize รายชื่อสาร
    # =========================================================================
    print("\n🧹 STEP 2: ดึงและ Normalize ชื่อสาร...")
    
    # ดึงส่วนผสมจาก raw text
    ingredients = extract_ingredients(raw_text)
    
    if not ingredients:
        print("❌ ไม่พบส่วนผสมในฉลาก")
        return {
            "status": "error",
            "message": "ไม่พบส่วนผสมในฉลาก กรุณาถ่ายภาพให้ชัดขึ้น",
            "cleaned_ingredients": [],
            "detected_allergens": [],
            "recommendation": "ไม่พบส่วนผสมในฉลาก",
            "ai_analysis": ""
        }
    
    print(f"✅ พบส่วนผสม {len(ingredients)} รายการ")
    
    # Normalize ชื่อสาร (แก้ไข OCR errors)
    print("⏳ กำลัง normalize ชื่อสาร...")
    try:
        normalized_results = normalize_ingredients(ingredients)
        
        # เก็บเฉพาะสารที่ normalize สำเร็จ
        normalized_ingredients = []
        for item in normalized_results:
            if item["corrected"] != "uncertain":
                normalized_ingredients.append(item["corrected"].upper())
            else:
                # ถ้า AI ไม่แน่ใจ ใช้ชื่อเดิม
                normalized_ingredients.append(item["original"].upper())
        
        print(f"✅ Normalize สำเร็จ {len(normalized_ingredients)} รายการ")
        
        # แสดง normalized ingredients
        print("\n📋 รายการสารที่ตรวจพบ:")
        for i, ing in enumerate(normalized_ingredients[:10], 1):
            print(f"   {i}. {ing}")
        if len(normalized_ingredients) > 10:
            print(f"   ... และอีก {len(normalized_ingredients) - 10} รายการ")
        
    except Exception as e:
        print(f"⚠️ Normalize ล้มเหลว: {e}")
        print("   → ใช้ชื่อดิบจาก OCR แทน")
        normalized_ingredients = [ing.upper() for ing in ingredients]
    
    # =========================================================================
    # 3️⃣ เปรียบเทียบกับสารที่ user แพ้ (Fuzzy Matching)
    # =========================================================================
    print("\n🔍 STEP 3: ค้นหาสารที่คุณแพ้...")
    
    if not user_allergies:
        print("ℹ️ ไม่มีข้อมูลสารที่แพ้")
        return {
            "status": "success",
            "message": "ไม่มีข้อมูลสารที่แพ้",
            "cleaned_ingredients": normalized_ingredients,
            "detected_allergens": [],
            "recommendation": "✅ ไม่มีข้อมูลสารที่แพ้ในระบบ",
            "ai_analysis": ""
        }
    
    print(f"🔴 สารที่คุณแพ้: {', '.join(user_allergies)}")
    
    # ใช้ Fuzzy Matching เพื่อหาสารที่แพ้
    matching_allergens = find_matching_allergens(user_allergies, normalized_ingredients)
    
    if not matching_allergens:
        print("✅ ไม่พบสารที่คุณแพ้ในผลิตภัณฑ์นี้")
        return {
            "status": "success",
            "message": "ปลอดภัย",
            "cleaned_ingredients": normalized_ingredients,
            "detected_allergens": [],
            "recommendation": "✅ ปลอดภัยสำหรับคุณ - ไม่พบสารที่คุณแพ้",
            "ai_analysis": ""
        }
    
    print(f"\n⚠️ พบสารที่คุณอาจแพ้: {len(matching_allergens)} รายการ")
    for match in matching_allergens:
        print(f"   🔴 {match['ingredient']} (ตรงกับ '{match['allergen']}' - {match['reason']})")
    
    # =========================================================================
    # 4️⃣ ให้ AI วิเคราะห์แต่ละสารที่แพ้
    # =========================================================================
    print("\n🧠 STEP 4: ให้ AI วิเคราะห์แต่ละสารที่แพ้...")
    print("⏳ กำลังรอ AI วิเคราะห์ (อาจใช้เวลา 1-3 นาที)...\n")
    
    try:
        ai_analysis = analyze_each_allergen(
            normalized_ingredients=normalized_ingredients,
            matching_allergens=matching_allergens
        )
        
        print("✅ AI วิเคราะห์เสร็จแล้ว!")
        
    except Exception as e:
        print(f"❌ AI วิเคราะห์ล้มเหลว: {e}")
        ai_analysis = {
            "status": "error",
            "raw_output": f"เกิดข้อผิดพลาด: {str(e)}",
            "analyzed_allergens": []
        }
    
    # =========================================================================
    # 5️⃣ รวมผลลัพธ์และสรุป
    # =========================================================================
    print("\n📊 STEP 5: สรุปผลลัพธ์...")
    
    # สร้าง detected_allergens สำหรับแสดงผล
    detected_allergens = []
    
    for match in matching_allergens:
        # หาข้อมูลจาก AI analysis
        ai_detail = next(
            (a for a in ai_analysis.get("analyzed_allergens", []) 
             if a.get("ingredient") == match["ingredient"]),
            None
        )
        
        if ai_detail:
            detected_allergens.append({
                "ingredient": match["ingredient"],
                "matched_allergen": match["allergen"],
                "match_reason": match["reason"],
                "risk_level": ai_detail.get("risk_level", "ไม่ทราบ"),
                "symptoms": ai_detail.get("symptoms", "ไม่ทราบ"),
                "recommendation": ai_detail.get("recommendation", "ควรระวัง"),
                "source": "ai_confirmed"
            })
        else:
            # ถ้า AI ไม่ได้วิเคราะห์ ให้ใช้ข้อมูลเบื้องต้น
            detected_allergens.append({
                "ingredient": match["ingredient"],
                "matched_allergen": match["allergen"],
                "match_reason": match["reason"],
                "risk_level": "ต้องตรวจสอบ",
                "symptoms": "ไม่ทราบ",
                "recommendation": "ควรระวัง",
                "source": "fuzzy_match_only"
            })
    
    # สรุปความเสี่ยง
    high_risk_count = sum(
        1 for a in detected_allergens 
        if "สูง" in a.get("risk_level", "").lower() or "high" in a.get("risk_level", "").lower()
    )
    
    if high_risk_count > 0:
        recommendation = f"🔴 ไม่ควรใช้ - พบสารที่คุณแพ้ {len(detected_allergens)} รายการ ({high_risk_count} รายการเสี่ยงสูง)"
    elif len(detected_allergens) > 0:
        recommendation = f"⚠️ ใช้ด้วยความระวัง - พบสารที่อาจทำให้แพ้ {len(detected_allergens)} รายการ"
    else:
        recommendation = "✅ ปลอดภัยสำหรับคุณ"
    
    print(f"\n{recommendation}")
    print("="*70 + "\n")
    
    return {
        "status": "success",
        "message": "วิเคราะห์สำเร็จ",
        "cleaned_ingredients": normalized_ingredients,
        "detected_allergens": detected_allergens,
        "recommendation": recommendation,
        "ai_analysis": ai_analysis.get("raw_output", "")
    }