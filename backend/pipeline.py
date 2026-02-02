from ocr_tess_test import ocr_image
from backend.ai_reasoning import process_with_ai

def run_pipeline(image_path, user_allergies=["ถั่ว", "Salicylic Acid"]): # สมมติค่าแพ้ของ User
    # 1. อ่านข้อความจากรูปเหมือนเดิม
    raw_text = ocr_image(image_path)
    
    # 2. ส่งให้ AI ประมวลผล (แทนที่ระบบ Regex และ DB เดิม)
    result = process_with_ai(raw_text, user_allergies)
    
    return result