import re

def fix_thai_spaced_text(text: str) -> str:
    """รวมอักษรไทยที่ถูก OCR แยกด้วยช่องว่าง และจัดการรอยต่อบรรทัด (-)"""
    # 1. จัดการคำภาษาอังกฤษที่ถูกตัดบรรทัดด้วย - เช่น STREPTACAN- THA
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # 2. รวมอักษรไทยที่แยกช่องว่าง
    text = re.sub(r'([ก-๙])\s+(?=[ก-๙])', r'\1', text)
    return text

# เพิ่ม Keyword เพื่อหยุดดึงข้อมูลทันทีเมื่อเจอคำพวกนี้
STOP_WORDS = [
    "วิธีใช้", "วิธีการใช้", "คำเตือน", "วิธีเก็บ", "การเก็บรักษา", 
    "ผลิตโดย", "จัดจำหน่าย", "เลขที่", "BATCH", "LOT", "MFG", "EXP",
    "บรรจุ", "ราคา", "ขนาด", "ข้อควรระวัง", "ประเภท", "ใบรับจดแจ้ง",
    "เลขที่จดแจ้ง", "MADE IN", "DISTRIBUTED", "MANUFACTURED"
]

def clean_ingredient_text(text: str) -> str:
    """ล้างสัญลักษณ์และช่องว่างขยะ"""
    text = re.sub(r'^[|.\'เ@\s:,\-?#+]+', '', text)
    text = re.sub(r'[.\'เ@\s:,\-?#+]+$', '', text)
    text = re.sub(r'\s+', ' ', text)
    # ลบตัวอักษรซ้ำขยะ เช่น eee, ..., ---
    if re.match(r'^([a-zA-Z.])\1+$', text): return ""
    return text.strip()

def is_valid_ingredient(text: str) -> bool:
    """คัดกรองว่าข้อความนี้คือชื่อสารจริงๆ หรือไม่"""
    # 1. ต้องมีตัวอักษร (อังกฤษหรือไทย)
    if not re.search(r'[a-zA-Zก-๙]', text): return False
    # 2. ต้องไม่ยาวเกินไป (ชื่อสารส่วนใหญ่ไม่เกิน 100 ตัวอักษรต่อหนึ่งตัว)
    if len(text) > 120: return False
    # 3. ต้องไม่มีตัวเลขเยอะเกินไป (ถ้าเป็นที่อยู่จะมีตัวเลขเยอะ)
    digit_count = sum(c.isdigit() for c in text)
    if digit_count > (len(text) * 0.3): return False # ถ้าตัวเลขเกิน 30% ของคำ คือขยะ
    # 4. กรองคำหยุดที่หลุดมาเป็นคำเดี่ยวๆ
    for stop in STOP_WORDS:
        if text == stop or len(text) < 2: return False
    return True

def extract_ingredients(ocr_text: str):
    # รวมข้อความที่ขาดออกจากกันก่อน
    text = fix_thai_spaced_text(ocr_text)
    
    start_idx = -1
    for kw in [
        "INGREDIENT", "ส่วนประกอบ", "ส่วนผสม", "สารสำคัญ", 
        "ดนประกอบ", "สว่นประกอบ", "วนประกอบ" # รวมคำที่ OCR มักอ่านผิด
    ]:
        matches = list(re.finditer(re.escape(kw), text, re.IGNORECASE))
        if matches:
            last_match = matches[-1]
            if last_match.start() > start_idx:
                start_idx = last_match.end()

    if start_idx == -1: return []

    raw_content = text[start_idx:].strip()
    # ตัดเครื่องหมายนำหน้า เช่น : หรือ -
    raw_content = re.sub(r'^[:\s\-]+', '', raw_content)

    # แยกส่วนผสมด้วย Comma หรือ Newline
    raw_ingredients = re.split(r',(?![^(]*\))|;|\n', raw_content)

    ingredients = []
    for ing in raw_ingredients:
        ing = clean_ingredient_text(ing)
        if not ing: continue

        # เช็ค Stop Words
        stop_found = False
        for stop in STOP_WORDS:
            if stop in ing:
                # ตัดเอาเฉพาะส่วนก่อนถึง Stop Word
                clean_part = clean_ingredient_text(ing.split(stop)[0])
                if is_valid_ingredient(clean_part):
                    ingredients.append(clean_part)
                stop_found = True
                break
        
        if stop_found: break
            
        if is_valid_ingredient(ing):
            ingredients.append(ing)

    return ingredients