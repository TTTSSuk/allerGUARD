from difflib import SequenceMatcher

def fuzzy_match(user_allergen, ingredient_name, threshold=0.75):
    """
    เปรียบเทียบชื่อสาร 2 ชื่อด้วย fuzzy matching
    
    Args:
        user_allergen: ชื่อสารที่ user กรอก (อาจพิมพ์ผิด)
        ingredient_name: ชื่อสารจาก OCR (ที่ normalize แล้ว)
        threshold: ค่าความคล้ายขั้นต่ำ (0.75 = 75%)
    
    Returns:
        dict: {"match": bool, "score": float, "reason": str}
    """
    
    # แปลงเป็นตัวพิมพ์ใหญ่ทั้งหมด
    allergen_upper = user_allergen.upper().strip()
    ingredient_upper = ingredient_name.upper().strip()
    
    # จัดการพหูพจน์ (ลบ S/ES ท้าย)
    allergen_singular = allergen_upper
    if allergen_upper.endswith('ES'):
        allergen_singular = allergen_upper[:-2]
    elif allergen_upper.endswith('S'):
        allergen_singular = allergen_upper[:-1]
    
    ingredient_singular = ingredient_upper
    if ingredient_upper.endswith('ES'):
        ingredient_singular = ingredient_upper[:-2]
    elif ingredient_upper.endswith('S'):
        ingredient_singular = ingredient_upper[:-1]
    
    # เงื่อนไข 1: ตรงทุกตัวอักษร (Exact Match)
    if allergen_upper == ingredient_upper:
        return {
            "match": True,
            "score": 1.0,
            "reason": "ตรงทุกตัวอักษร"
        }
    
    # เงื่อนไข 2: user พิมพ์ไม่ครบ แต่เป็น substring (เช่น "SALICY" ใน "SALICYLIC ACID")
    if allergen_upper in ingredient_upper:
        score = len(allergen_upper) / len(ingredient_upper)
        if score >= 0.5:  # ต้องพิมพ์อย่างน้อย 50% ของชื่อจริง
            return {
                "match": True,
                "score": score,
                "reason": f"พิมพ์ไม่ครบ (พิมพ์ {len(allergen_upper)}/{len(ingredient_upper)} ตัว)"
            }
    
    # เงื่อนไข 3: ingredient มีคำที่ user พิมพ์ (เช่น "ACID" ใน "SALICYLIC ACID")
    if ingredient_upper in allergen_upper:
        score = len(ingredient_upper) / len(allergen_upper)
        if score >= 0.5:
            return {
                "match": True,
                "score": score,
                "reason": f"ชื่อสารมีคำที่คุณพิมพ์"
            }
    
    # เงื่อนไข 3.5: user พิมพ์เป็นส่วนหนึ่งของคำในชื่อสาร (เช่น "PARABEN" ใน "METHYLPARABEN")
    # ต้องตรงอย่างน้อย 50% ของคำที่ user พิมพ์
    if len(allergen_upper) >= 5:  # ต้องพิมพ์อย่างน้อย 5 ตัวอักษร
        for word in ingredient_upper.split():
            # ลองทั้ง word ปกติและ singular form ของ word
            word_singular = word
            if word.endswith('ES'):
                word_singular = word[:-2]
            elif word.endswith('S'):
                word_singular = word[:-1]
            
            # เช็คทั้ง allergen_upper และ allergen_singular กับ word และ word_singular
            for allergen_form in [allergen_upper, allergen_singular]:
                for word_form in [word, word_singular]:
                    if allergen_form in word_form:
                        score = len(allergen_form) / len(word_form)
                        if score >= 0.5:  # ลดจาก 0.6 เป็น 0.5
                            return {
                                "match": True,
                                "score": score,
                                "reason": f"พบคำว่า '{allergen_form}' ในส่วนของ '{word}'"
                            }
    
    # เงื่อนไข 4: Fuzzy matching ด้วย SequenceMatcher (จัดการ typo)
    similarity = SequenceMatcher(None, allergen_upper, ingredient_upper).ratio()
    
    if similarity >= threshold:
        return {
            "match": True,
            "score": similarity,
            "reason": f"คล้ายกัน {int(similarity*100)}% (อาจพิมพ์ผิด)"
        }
    
    # เงื่อนไข 5: เช็คทีละคำ (สำหรับชื่อสารที่มีหลายคำ)
    allergen_words = allergen_upper.split()
    ingredient_words = ingredient_upper.split()
    
    # กรองคำทั่วไปที่ไม่ควรใช้จับคู่ (ACID, GLYCOL, EXTRACT, OIL, WATER, etc.)
    COMMON_WORDS = {'ACID', 'GLYCOL', 'EXTRACT', 'OIL', 'WATER', 'AQUA', 'BUTTER', 
                    'OXIDE', 'CHLORIDE', 'SULFATE', 'ACETATE', 'ALCOHOL'}
    
    # กรองคำทั่วไปออก
    allergen_specific = [w for w in allergen_words if w not in COMMON_WORDS]
    ingredient_specific = [w for w in ingredient_words if w not in COMMON_WORDS]
    
    # ถ้า user พิมพ์ 1 คำ ให้เช็คว่าตรงกับคำไหนใน ingredient ไหม
    if len(allergen_words) == 1:
        # ถ้าเป็นคำทั่วไป (เช่น "acid") ไม่ให้จับ
        if allergen_upper in COMMON_WORDS:
            return {
                "match": False,
                "score": 0,
                "reason": "คำทั่วไปเกินไป (ต้องระบุชื่อสารหลัก)"
            }
        
        for word in ingredient_words:
            word_similarity = SequenceMatcher(None, allergen_upper, word).ratio()
            if word_similarity >= threshold:
                return {
                    "match": True,
                    "score": word_similarity,
                    "reason": f"ตรงกับคำ '{word}' ในชื่อสาร ({int(word_similarity*100)}%)"
                }
    
    # ถ้า user พิมพ์หลายคำ ให้เช็คคำเฉพาะ (ไม่ใช่คำทั่วไป)
    if len(allergen_words) > 1 and len(allergen_specific) > 0:
        matching_words = 0
        matched_specific = 0
        
        for allergen_word in allergen_words:
            is_specific = allergen_word in allergen_specific
            
            for ingredient_word in ingredient_words:
                if SequenceMatcher(None, allergen_word, ingredient_word).ratio() >= threshold:
                    matching_words += 1
                    if is_specific:
                        matched_specific += 1
                    break
        
        # ต้องมีคำเฉพาะตรงอย่างน้อย 1 คำ (ไม่ให้จับแค่ ACID ตรง)
        if matched_specific > 0 and matching_words >= len(allergen_words) * 0.5:
            return {
                "match": True,
                "score": matching_words / len(allergen_words),
                "reason": f"ตรง {matching_words}/{len(allergen_words)} คำ"
            }
    
    # ไม่ match
    return {
        "match": False,
        "score": similarity,
        "reason": "ไม่ตรงกัน"
    }


def find_matching_allergens(user_allergies, normalized_ingredients):
    """
    หาสารที่ user แพ้จาก list ส่วนผสม
    
    Args:
        user_allergies: list ของชื่อสารที่ user แพ้
        normalized_ingredients: list ของชื่อสารจาก OCR (normalize แล้ว)
    
    Returns:
        list: [{"allergen": str, "ingredient": str, "match_score": float, "reason": str}]
    """
    
    matches = []
    
    for allergen in user_allergies:
        for ingredient in normalized_ingredients:
            result = fuzzy_match(allergen, ingredient, threshold=0.75)
            
            if result["match"]:
                matches.append({
                    "allergen": allergen,  # ชื่อที่ user พิมพ์
                    "ingredient": ingredient,  # ชื่อจริงในผลิตภัณฑ์
                    "match_score": result["score"],
                    "reason": result["reason"]
                })
                
                print(f"✅ Match: '{allergen}' → '{ingredient}' ({result['reason']})")
    
    return matches


# ทดสอบ
if __name__ == "__main__":
    # Test cases
    test_cases = [
        # (user input, ingredient name, should_match)
        ("SALICY", "SALICYLIC ACID", True),  # พิมพ์ไม่ครบ
        ("salicylic acid", "SALICYLIC ACID", True),  # ตัวเล็ก
        ("Salicylic 0cid", "SALICYLIC ACID", True),  # พิมพ์ผิด
        ("PARABENS", "METHYLPARABEN", True),  # substring
        ("GLYCOLIC", "GLYCOLIC ACID", True),  # พิมพ์ไม่ครบ
        ("RETINOL", "RETINOL", True),  # ตรงเป๊ะ
        ("VITAMIN C", "ASCORBIC ACID", False),  # ไม่ตรง
        ("sorbic acid", "SALICYLIC ACID", False),  # ไม่ควรจับ (แก้ไขแล้ว)
        ("sorbic acid", "SORBIC ACID", True),  # ควรจับ
    ]
    
    print("🧪 Testing Fuzzy Matcher...\n")
    
    for user_input, ingredient, expected in test_cases:
        result = fuzzy_match(user_input, ingredient)
        status = "✅" if result["match"] == expected else "❌"
        print(f"{status} '{user_input}' vs '{ingredient}'")
        print(f"   → Match: {result['match']}, Score: {result['score']:.2f}, Reason: {result['reason']}\n")