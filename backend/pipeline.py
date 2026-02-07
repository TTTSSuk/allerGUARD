from ocr_tess_test import ocr_image
from ingredient_extractor import extract_ingredients
from ai_normalize import normalize_ingredients
from ai_reasoning import process_with_ai
import re

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

    # 3. ตรวจ allergen แบบ Exact + Partial matching
    detected_exact = []
    detected_partial = []
    user_allergies_upper = [u.upper() for u in user_allergies]

    for ing in normalized_ingredients:
        for allergy in user_allergies_upper:
            # Exact Match - ตรงทุกตัวอักษร
            if allergy == ing:
                detected_exact.append({
                    "ingredient": ing,
                    "matched_allergen": allergy,
                    "reason": f"ตรงกับ '{allergy}' ทุกตัวอักษร",
                    "level": "HIGH",
                    "confidence": "แน่นอน",
                    "source": "exact_match"
                })
                break
            # Partial Match - ต้องให้ AI ตรวจสอบ
            elif allergy in ing:
                detected_partial.append({
                    "ingredient": ing,
                    "matched_allergen": allergy,
                    "reason": f"พบคำว่า '{allergy}' ในชื่อสาร",
                    "level": "UNKNOWN",
                    "confidence": "ต้องตรวจสอบ",
                    "source": "partial_match"
                })
                break

    # 4. ให้ AI วิเคราะห์
    ai_output = ""
    ai_confirmed = []
    ai_cross_reactive = []
    ai_false_positive = []
    
    if user_allergies and (detected_exact or detected_partial):
        try:
            print("🤖 ให้ AI วิเคราะห์แบบครบถ้วน...")
            
            to_verify = detected_exact + detected_partial
            
            ai_result = process_with_ai(
                normalized_ingredients, 
                user_allergies, 
                to_verify
            )
            ai_output = ai_result.get("raw_ai_output", "")
            
            # 🔥 DEBUG: แสดง AI output
            print("\n" + "="*70)
            print("🤖 AI RAW OUTPUT:")
            print("="*70)
            print(ai_output)
            print("="*70 + "\n")
            
            # Parse AI output
            print("🔍 กำลัง parse AI response...")
            ai_confirmed, ai_cross_reactive, ai_false_positive = parse_ai_response(
                ai_output, 
                detected_partial
            )
            print(f"✅ Parse เสร็จ: confirmed={len(ai_confirmed)}, cross={len(ai_cross_reactive)}, false={len(ai_false_positive)}\n")
    
        except Exception as e:
            print(f"⚠️ AI Error: {e}")
            ai_output = f"AI วิเคราะห์ไม่สำเร็จ: {str(e)}"

    # 5. รวมผลลัพธ์
    all_detected = []
    
    # เพิ่ม Exact Match
    for item in detected_exact:
        all_detected.append({
            **item,
            "category": "แพ้แน่นอน"
        })
    
    # เพิ่ม AI Confirmed (จาก Partial)
    for item in ai_confirmed:
        if not any(d["ingredient"] == item["ingredient"] for d in detected_exact):
            all_detected.append({
                **item,
                "category": "แพ้จริง (AI ยืนยัน)"
            })
    
    # เพิ่ม Cross-reactive
    for item in ai_cross_reactive:
        all_detected.append({
            **item,
            "category": "อาจแพ้ไขว้"
        })
    
    # เพิ่ม False Positive (สำหรับแสดงว่าไม่เกี่ยวข้อง)
    for item in ai_false_positive:
        all_detected.append({
            **item,
            "category": "ไม่เกี่ยวข้อง"
        })
    
    # 6. สรุปผล
    recommendation = ""
    if all_detected:
        high_risk = [d for d in all_detected 
                    if d.get("level", "").upper() in ["HIGH", "MEDIUM"] 
                    and d.get("category") != "ไม่เกี่ยวข้อง"]
        
        if high_risk:
            recommendation = f"🔴 พบสารที่แพ้ {len(high_risk)} รายการ - ควรหลีกเลี่ยง"
        else:
            recommendation = "✅ ปลอดภัยสำหรับคุณ"
    else:
        recommendation = "✅ ปลอดภัยสำหรับคุณ"

    return {
        "status": "success",
        "cleaned_ingredients": normalized_ingredients,
        "detected_allergens": all_detected,
        "recommendation": recommendation,
        "ai_analysis": ai_output
    }


def parse_ai_response(ai_output, partial_matches):
    """แยก AI response เป็น 3 กลุ่ม: confirmed, cross-reactive, false-positive"""
    
    confirmed = []
    cross_reactive = []
    false_positive = []
    
    print(f"   📄 AI output length: {len(ai_output)} chars")
    print(f"   📝 Partial matches to verify: {len(partial_matches)}")
    
    if not ai_output or len(ai_output) < 50:
        print("   ⚠️ AI output ว่างหรือสั้นเกินไป!")
        return confirmed, cross_reactive, false_positive
    
    # แยก sections
    sections = ai_output.split("2️⃣")
    print(f"   🔢 Sections found: {len(sections)}")
    
    # Section 1: สารที่แพ้โดยตรง
    if len(sections) > 0:
        direct_section = sections[0]
        
        # ลอง pattern หลายแบบ
        patterns = [
            r'🔴\s+([A-Z\s\(\)\-\/]+?)\s+\(ตำแหน่ง\s+(\d+)/(\d+)\)',
            r'🔴\s+([A-Z\s\(\)\-\/]+?)[\n\r]',
        ]
        
        direct_matches = []
        for i, pattern in enumerate(patterns):
            direct_matches = re.findall(pattern, direct_section, re.MULTILINE)
            if direct_matches:
                print(f"   ✅ Pattern {i+1} matched! Found {len(direct_matches)} direct allergens")
                break
        
        for match in direct_matches:
            if isinstance(match, tuple) and len(match) >= 3:
                ing_name = match[0].strip()
                position = match[1]
                total = match[2]
            elif isinstance(match, tuple):
                ing_name = match[0].strip()
                position = "?"
                total = "?"
            else:
                ing_name = match.strip()
                position = "?"
                total = "?"
            
            # ดึงระดับความเสี่ยง
            pattern = rf'{re.escape(ing_name)}.*?ความเสี่ยง:\s+(\S+)'
            risk_match = re.search(pattern, direct_section, re.DOTALL)
            risk_level = risk_match.group(1).strip() if risk_match else "สูง"
            
            # แปลงภาษาไทยเป็นภาษาอังกฤษ
            risk_map = {
                "สูงมาก": "VERY_HIGH",
                "สูง": "HIGH", 
                "ปานกลาง": "MEDIUM",
                "ต่ำ": "LOW",
                "ต่ำมาก": "VERY_LOW"
            }
            risk_eng = risk_map.get(risk_level, risk_level.upper())
            
            confirmed.append({
                "ingredient": ing_name,
                "reason": f"AI ยืนยัน - เป็นสารที่แพ้ (ตำแหน่ง {position}/{total})",
                "level": risk_eng,
                "confidence": "สูง",
                "source": "ai_confirmed"
            })
    
    # Section 2: Cross-reactivity
    if len(sections) > 1:
        cross_section = sections[1].split("3️⃣")[0] if "3️⃣" in sections[1] else sections[1]
        
        if "ไม่พบ" not in cross_section and "✅" not in cross_section:
            cross_patterns = [
                r'🟡\s+([A-Z\s\(\)\-\/]+?)\s+\(ตำแหน่ง\s+(\d+)/(\d+)\)',
                r'🟡\s+([A-Z\s\(\)\-\/]+?)[\n\r]',
            ]
            
            cross_matches = []
            for i, pattern in enumerate(cross_patterns):
                cross_matches = re.findall(pattern, cross_section, re.MULTILINE)
                if cross_matches:
                    print(f"   ✅ Cross-reactive pattern {i+1} matched! Found {len(cross_matches)} items")
                    break
            
            for match in cross_matches:
                if isinstance(match, tuple) and len(match) >= 3:
                    ing_name = match[0].strip()
                    position = match[1]
                    total = match[2]
                elif isinstance(match, tuple):
                    ing_name = match[0].strip()
                    position = "?"
                    total = "?"
                else:
                    ing_name = match.strip()
                    position = "?"
                    total = "?"
                
                pattern = rf'{re.escape(ing_name)}.*?เหตุผล:\s+(.+?)(?:→|ความเสี่ยง|$)'
                reason_match = re.search(pattern, cross_section, re.DOTALL)
                reason = reason_match.group(1).strip() if reason_match else "อาจแพ้ไขว้"
                
                cross_reactive.append({
                    "ingredient": ing_name,
                    "reason": f"{reason} (ตำแหน่ง {position}/{total})",
                    "level": "MEDIUM",
                    "confidence": "ปานกลาง",
                    "source": "ai_cross_reactive"
                })
    
    # หา False Positives (Partial matches ที่ AI ไม่ได้ยืนยัน)
    confirmed_names = {item["ingredient"] for item in confirmed}
    cross_names = {item["ingredient"] for item in cross_reactive}
    
    for pm in partial_matches:
        if pm["ingredient"] not in confirmed_names and pm["ingredient"] not in cross_names:
            false_positive.append({
                "ingredient": pm["ingredient"],
                "reason": f"AI ตรวจสอบแล้ว - ไม่เกี่ยวกับ '{pm['matched_allergen']}'",
                "level": "SAFE",
                "confidence": "AI ยืนยัน",
                "source": "ai_false_positive"
            })
    
    return confirmed, cross_reactive, false_positive