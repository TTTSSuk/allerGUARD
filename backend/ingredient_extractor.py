import re

def normalize_text(text: str) -> str:
    # รวมช่องว่างที่ OCR แตก
    text = " ".join(text.split())

    # แก้ pattern ที่ OCR พังบ่อย
    text = text.replace(" / ", "/")
    text = text.replace("( ", "(").replace(" )", ")")
    text = text.replace(" ,", ",")
    text = text.replace("/ ", "/").replace(" /", "/")
    text = text.replace(" ppm", "ppm")

    return text

# Stop words ที่บอกว่าส่วน INGREDIENTS จบแล้ว
STOP_WORDS = [
    # ภาษาไทย (รวมทั้งแบบมีช่องว่างจาก OCR)
    "วิธี", "ว ิ ธ ี", "วิ ธ ี", "ว ิธี",
    "การใช้", "ก า ร ใ ช ้", "การ ใช้",
    "เก็บ", "เ ก ็ บ", "รักษา", "ร ั ก ษ า",
    "ผลิต", "ผ ล ิ ต", "ผล ิต",
    "นำเข้า", "น ํ า เ ข ้ า", "นํา เข้า",
    "จัดจำหน่าย", "จ ั ด จ ํ า ห น ่ า ย",
    "ราคา", "ร า ค า",
    "เลขที่", "เ ล ข ท ี ่",
    "บรรจุ", "บ ร ร จ ุ",
    
    # ภาษาอังกฤษ
    "METHOD", "HOW TO", "STORAGE", "DIRECTION",
    "MANUFACTURED BY", "IMPORTED BY", "DISTRIBUTED BY",
    "PRICE", "NET WEIGHT", "BATCH", "LOT",
    "PRODUCT OF", "MADE IN",
    
    # อื่นๆ
    "OTHER", "@", "facebook", "instagram", "www",
    "Co.", "Ltd", "Company", "Inc"
]

def extract_ingredients(ocr_text: str):
    """
    ดึงส่วนผสมจาก OCR text โดยหาจาก INGREDIENT และตัดส่วนที่ไม่เกี่ยวข้องออก
    """
    # รวม newline เป็น space และลบช่องว่างซ้ำ
    text = normalize_text(ocr_text)

    # ดึงเฉพาะหลัง INGREDIENT
    match = re.search(
        r'INGREDIENTS?\s*:?\s*(.+)',
        text,
        re.IGNORECASE
    )

    if not match:
        return []

    ingredient_block = match.group(1)

    # ตัดเมื่อเจอ stop word
    # แบบ simple: หา index แรกสุดที่มี stop word (ไม่ใช้ word boundary)
    # earliest_stop = len(ingredient_block)
    # for stop in STOP_WORDS:
    #     idx = ingredient_block.find(stop)
    #     if idx != -1:
    #         earliest_stop = min(earliest_stop, idx)
    earliest_stop = len(ingredient_block)
    lower_block = ingredient_block.lower()
    for stop in STOP_WORDS:
        idx = lower_block.find(stop.lower())
        if idx != -1:
            earliest_stop = min(earliest_stop, idx)

    ingredient_block = ingredient_block[:earliest_stop]

    # แยกด้วย comma แต่รวม fragment ที่ขาดไป (เช่น ppm, %)
    raw_ingredients = ingredient_block.split(",")
    
    # รวม fragment ที่เป็นหน่วย (ppm, %) กับตัวก่อนหน้า
    merged_ingredients = []
    i = 0
    while i < len(raw_ingredients):
        ing = raw_ingredients[i].strip()
        
        # ถ้า fragment ถัดไปเป็นตัวเลข + หน่วย -> รวมเข้า
        # รองรับ pattern: "900ppm)", "5,900ppm)", "10%", etc.
        if i + 1 < len(raw_ingredients):
            next_part = raw_ingredients[i + 1].strip()
            # ตรวจว่าเป็นแค่ตัวเลข/เครื่องหมาย + หน่วย (ไม่มีตัวอักษรชื่อสารอื่น)
            if next_part and re.match(r'^[\d\s,.\-()]*(?:ppm|%|mg|g|ml|mcg|iu)[\s)]*$', next_part, re.IGNORECASE):
                ing += "," + next_part
                i += 1  # skip next
        
        merged_ingredients.append(ing)
        i += 1

    ingredients = []
    for ing in merged_ingredients:
        ing = ing.strip()

        # กรองของแปลก
        if len(ing) < 3:
            continue
        if any(word.lower() in ing.lower() for word in ["http", "www", "@", "facebook", "instagram"]):
            continue
        
        # กรองตัวเลขล้วน ๆ
        clean_ing = ing.replace(".", "").replace("-", "").replace(",", "").replace(" ", "")
        if clean_ing.replace("ppm", "").replace("%", "").isdigit():
            continue
        
        # กรองถ้ามีตัวเลขเกิน 50% (อาจเป็นรหัสผลิตภัณฑ์)
        digit_count = sum(c.isdigit() for c in ing)
        if digit_count > len(ing) * 0.5:
            continue
        
        # กรองข้อความที่มีภาษาไทย (ซึ่งมักเป็นคำอธิบายภายหลัง)
        thai_chars = sum('\u0e00' <= c <= '\u0e7f' for c in ing)
        if thai_chars > 3:  # มีภาษาไทยมากกว่า 3 ตัว
            continue

        ingredients.append(ing)

    return ingredients