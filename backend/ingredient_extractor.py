import re

def fix_common_ocr_errors(text: str) -> str:
    """แก้ไขข้อผิดพลาดทั่วไปจาก OCR"""
    
    # แก้คำที่ OCR อ่านผิดบ่อย - ทำก่อนทุกอย่าง
    replacements = {
        # ACID ที่ถูกอ่านผิด
        r'\bpid\b': 'ACID',
        r'\b0\s*ได\s*acid\b': 'SALICYLIC ACID',
        r'\b0\s*ได\b': 'SALICYLIC',
        r'\'Acid\b': 'ACID',  # 'Acid → ACID
        
        # GLYCOL ที่ถูกอ่านผิด
        r'\bwool\b': 'GLYCOL',
        r'\bCapryly\s+wool\b': 'CAPRYLYL GLYCOL',
        r'\bCapryly\b': 'CAPRYLYL',
        
        # LEAF ที่ถูกอ่านผิด
        r'\bleal\b': 'LEAF',
        r'\bLeaf\s+leal\b': 'LEAF',
        
        # EXTRACT ที่ถูกอ่านผิด
        r'\bwer\s+Extract\b': 'EXTRACT',
        r'\bwer\b(?=\s*,|\s*\.)': 'EXTRACT',
        
        # ชื่อสารที่อ่านผิด
        r'\bexyiglycerin\b': 'ETHYLHEXYLGLYCERIN',
        r'\bbirlower\b': 'SAFFLOWER',
        r'\bAlternifolio\b': 'ALTERNIFOLIA',
        r'\bCentelia\b': 'CENTELLA',
        r'\bNobili\b': 'NOBILIS',
        r'\bCameliia\b': 'CAMELLIA',
        r'\blsomerized\b': 'ISOMERIZED',
        r'\bPalmitoy\'\b': 'PALMITOYL',
        
        # ลบตัวอักษรเดี่ยวที่เป็นขยะ
        r'\bAi,\s+': '',
        r'\bM,\s+': '',
        r'\bq\s+': '',
        
        # คำไทยที่ไม่ควรอยู่ในชื่อสาร
        r'สหกรดตทานทา\s+': '',
        r'ตร์ญ่\s+': '',
        r'ไผดิอน\s+\d+': '',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def fix_thai_spaced_text(text: str) -> str:
    """รวมอักษรไทยที่ถูก OCR แยกด้วยช่องว่าง และจัดการรอยต่อบรรทัด"""
    
    # 1. จัดการคำภาษาอังกฤษที่ถูกตัดบรรทัด
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 2. รวม ACID/GLYCOL ที่ถูกแยก (ต้องทำก่อนการแยก comma)
    text = re.sub(r'\b(HYALURONIC|SALICYLIC|ASCORBIC|PALMITIC|STEARIC|CITRIC|LACTIC|GLYCOLIC|SAFFLOWER)\s+ACID\b', 
                  r'\1 ACID', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(BUTYLENE|PROPYLENE|ETHYLENE|HEXYLENE|CAPRYLYL|DIPROPYLENE)\s+GLYCOL\b', 
                  r'\1 GLYCOL', text, flags=re.IGNORECASE)
    
    # 3. รวมชื่อสารที่มักถูกแยก
    common_compounds = [
        (r'\b(MELALEUCA)\s+(ALTERNIFOLIA)\b', r'\1 \2'),
        (r'\b(TEA)\s+(TREE)\b', r'\1 \2'),
        (r'\b(SHEA)\s+(BUTTER)\b', r'\1 \2'),
        (r'\b(ANTHEMIS)\s+(NOBILIS)\b', r'\1 \2'),
        (r'\b(FUCUS)\s+(VESICULOSUS)\b', r'\1 \2'),
        (r'\b(CAMELLIA)\s+(SINENSIS)\b', r'\1 \2'),
    ]
    
    for pattern, replacement in common_compounds:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # 4. รวมอักษรไทยที่แยกช่องว่าง
    text = re.sub(r'([ก-๙])\s+(?=[ก-๙])', r'\1', text)
    
    return text

# Stop Words
STOP_WORDS = [
    "วิธีใช้", "วิธีการใช้", "คำเตือน", "วิธีเก็บ", "การเก็บรักษา", 
    "ผลิตโดย", "จัดจำหน่าย", "เลขที่", "BATCH", "LOT", "MFG", "EXP",
    "บรรจุ", "ราคา", "ขนาด", "ข้อควรระวัง", "ประเภท", 
    "MADE IN", "DISTRIBUTED", "MANUFACTURED", "IMPORTED",
    "ระวัง", "ห้าม", "หมายเหตุ", "ห้ามใช้", "หยุดใช้", "ไผดิอน",
    "DIRECTIONS", "DIRECTION", "HOW TO USE", "USAGE"
]

# คำขยะจาก OCR
JUNK_WORDS = [
    "wool", "Ai", "pid", "wer", "nr", "a4", "oa", "coe",
    "rites", "oes", "แฟกซี", "Bae", "Oe", "Se", "Ay", "Yr"
]

def clean_ingredient_text(text: str) -> str:
    """ล้างสัญลักษณ์และช่องว่างขยะ"""
    
    # ลบสัญลักษณ์ขยะ
    text = re.sub(r'^[|.\'เ@\s:,\-?#+]+', '', text)
    text = re.sub(r'[.\'เ@\s:,\-?#+]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # ลบตัวอักษรซ้ำ
    if re.match(r'^([a-zA-Z.])\1+$', text): 
        return ""
    
    # ลบวงเล็บว่าง
    text = re.sub(r'\(\s*\)', '', text)
    
    # ลบตัวเลขเดี่ยวๆ
    if re.match(r'^\d+\.?$', text):
        return ""
    
    return text.strip()

def is_valid_ingredient(text: str) -> bool:
    """ตรวจสอบว่าเป็นชื่อสารจริงหรือไม่"""
    
    if not text:
        return False
    
    # ต้องมีตัวอักษร
    if not re.search(r'[a-zA-Zก-๙]', text): 
        return False
    
    # ความยาวเหมาะสม
    if len(text) < 2 or len(text) > 120: 
        return False
    
    # ไม่มีตัวเลขมากเกินไป
    digit_count = sum(c.isdigit() for c in text)
    if digit_count > (len(text) * 0.4): 
        return False
    
    # กรองคำขยะ
    text_lower = text.lower()
    for junk in JUNK_WORDS:
        if text_lower == junk.lower():
            return False
    
    # กรอง Stop Words
    for stop in STOP_WORDS:
        if stop.lower() in text_lower:
            return False
    
    # ไม่มีอักษรไทยปนอังกฤษ (ยกเว้นในวงเล็บ)
    text_no_paren = text.replace('(', '').replace(')', '')
    if re.search(r'[ก-๙]+[a-zA-Z]+|[a-zA-Z]+[ก-๙]+', text_no_paren):
        return False
    
    # กรองประโยคคำสั่ง
    instruction_keywords = ['then', 'wait', 'rinse', 'spread', 'open', 'leave on']
    for keyword in instruction_keywords:
        if keyword in text_lower:
            return False
    
    return True

def split_merged_ingredients(text: str) -> list:
    """แยกส่วนผสมที่ติดกันออกจากกัน"""
    
    # กรณีที่มี comma แฝงอยู่ในบรรทัดเดียว (เช่น "A, B, C")
    if ',' in text:
        parts = [p.strip() for p in text.split(',')]
        return [p for p in parts if p]
    
    # ไม่มี comma แต่มีหลายชื่อสารติดกัน
    # หาจุดที่น่าจะเป็นการขึ้นชื่อสารใหม่
    
    # Pattern 1: ชื่อสารขึ้นต้นด้วยตัวพิมพ์ใหญ่หลังจากคำที่ลงท้ายด้วย ACID, GLYCOL, EXTRACT, etc.
    endings = r'\b(ACID|GLYCOL|EXTRACT|OIL|BUTTER|OXIDE|CHLORIDE|SULFATE|ACETATE|HYDROXIDE)\s+'
    parts = re.split(endings, text, flags=re.IGNORECASE)
    
    result = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts) and parts[i+1].upper() in ['ACID', 'GLYCOL', 'EXTRACT', 'OIL', 'BUTTER', 
                                                          'OXIDE', 'CHLORIDE', 'SULFATE', 'ACETATE', 'HYDROXIDE']:
            # รวมชื่อสาร + ending
            combined = (parts[i] + ' ' + parts[i+1]).strip()
            if combined:
                result.append(combined)
            i += 2
        else:
            if parts[i].strip():
                result.append(parts[i].strip())
            i += 1
    
    # ถ้าไม่ได้แยกอะไร ให้คืนค่าเดิม
    if len(result) <= 1:
        return [text]
    
    return result

def extract_ingredients(ocr_text: str):
    """ดึงส่วนผสมจาก OCR text"""
    
    # 1. แก้ไข OCR errors
    text = fix_common_ocr_errors(ocr_text)
    
    # 2. รวมข้อความที่ถูกแยก
    text = fix_thai_spaced_text(text)
    
    # 3. หาจุดเริ่มต้น
    start_idx = -1
    ingredient_keywords = [
        "INGREDIENT", "ส่วนประกอบ", "ส่วนผสม", "สารสำคัญ", 
        "ดนประกอบ", "สว่นประกอบ", "วนประกอบ"
    ]
    
    for kw in ingredient_keywords:
        matches = list(re.finditer(re.escape(kw), text, re.IGNORECASE))
        if matches:
            last_match = matches[-1]
            if last_match.start() > start_idx:
                start_idx = last_match.end()

    if start_idx == -1: 
        return []

    raw_content = text[start_idx:].strip()
    raw_content = re.sub(r'^[:\s\-]+', '', raw_content)

    # 4. แยกส่วนผสมด้วย comma, semicolon, newline
    raw_ingredients = re.split(r',(?![^(]*\))|;|\n', raw_content)

    ingredients = []
    
    for ing in raw_ingredients:
        ing = clean_ingredient_text(ing)
        if not ing: 
            continue

        # เช็ค Stop Words
        stop_found = False
        for stop in STOP_WORDS:
            if stop.lower() in ing.lower():
                # เก็บส่วนก่อน Stop Word
                parts = re.split(stop, ing, flags=re.IGNORECASE)
                if len(parts) > 0:
                    clean_part = clean_ingredient_text(parts[0])
                    if clean_part and is_valid_ingredient(clean_part):
                        # ลองแยกเผื่อมีหลายส่วนผสมติดกัน
                        sub_parts = split_merged_ingredients(clean_part)
                        for sp in sub_parts:
                            sp_clean = clean_ingredient_text(sp)
                            if sp_clean and is_valid_ingredient(sp_clean):
                                ingredients.append(sp_clean)
                stop_found = True
                break
        
        if stop_found: 
            break
        
        # ตรวจสอบและแยกส่วนผสมที่ติดกัน
        if is_valid_ingredient(ing):
            # ลองแยกเผื่อมีหลายส่วนผสมในบรรทัดเดียว
            sub_parts = split_merged_ingredients(ing)
            
            for part in sub_parts:
                part_clean = clean_ingredient_text(part)
                if part_clean and is_valid_ingredient(part_clean):
                    ingredients.append(part_clean)

    # 5. รวมส่วนผสมที่ถูกแยก (EXTRACT, ACID, etc. ที่อยู่คนละบรรทัด)
    merged = []
    i = 0
    
    while i < len(ingredients):
        current = ingredients[i]
        
        # ถ้าเป็น EXTRACT/ACID/GLYCOL เดี่ยวๆ ให้รวมกับตัวก่อนหน้า
        if current.upper() in ['EXTRACT', 'ACID', 'GLYCOL', 'OIL', 'BUTTER'] and len(merged) > 0:
            merged[-1] = f"{merged[-1]} {current}"
            i += 1
            continue
        
        # ถ้าตัวถัดไปเป็น EXTRACT/ACID/GLYCOL ให้รวมกับตัวปัจจุบัน
        if i + 1 < len(ingredients):
            next_item = ingredients[i + 1]
            if next_item.upper() in ['EXTRACT', 'ACID', 'GLYCOL', 'OIL', 'BUTTER']:
                merged.append(f"{current} {next_item}")
                i += 2
                continue
        
        merged.append(current)
        i += 1
    
    return merged

def format_ingredients_output(ingredients: list) -> str:
    """จัดรูปแบบการแสดงผล"""
    if not ingredients:
        return "❌ ไม่พบส่วนผสมในภาพ"
    
    output = "🧪 ส่วนผสมที่ตรวจพบ:\n\n"
    for idx, ing in enumerate(ingredients, 1):
        output += f"{idx}. {ing}\n"
    
    return output