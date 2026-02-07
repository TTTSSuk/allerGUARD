from pipeline import run_pipeline

image_path = "D:\\allerGUARD\\sample_images\\label3.jpg"

print("\n" + "="*70)
print("🛡️  AllerGUARD - ระบบตรวจสารแพ้ในเครื่องสำอาง")
print("="*70)

print("\n📸 กำลังวิเคราะห์ผลิตภัณฑ์...")

result = run_pipeline(
    image_path, 
    user_allergies=["curcuma", 
                    "lactose", 
                    "salicylic", 
                    "palmitic",
                    "Essential oils",
                    "madecassoside",
                    "niacinamide",
                    "BENZYL ALCOHOL",
                    "PARFUM"]
)

# ========== 1. แสดงส่วนผสมก่อน ==========
print("\n" + "="*70)
print(f"📋 ส่วนผสมทั้งหมด ({len(result['cleaned_ingredients'])} รายการ)")
print("="*70)
for idx, ing in enumerate(result["cleaned_ingredients"], 1):
    print(f"{idx:2d}. {ing}")

# ========== 2. แสดงผลการตรวจสอบสารแพ้ ==========
print("\n" + "="*70)
print("🔍 ผลการตรวจสอบสารแพ้")
print("="*70)

if result["detected_allergens"]:
    # จัดกลุ่ม
    exact = [r for r in result["detected_allergens"] if r.get("category") == "แพ้แน่นอน"]
    confirmed = [r for r in result["detected_allergens"] if r.get("category") == "แพ้จริง (AI ยืนยัน)"]
    cross = [r for r in result["detected_allergens"] if r.get("category") == "อาจแพ้ไขว้"]
    false_pos = [r for r in result["detected_allergens"] if r.get("category") == "ไม่เกี่ยวข้อง"]
    
    # แสดงสารที่แพ้แน่นอน
    if exact:
        print("\n🔴 สารที่แพ้แน่นอน (ตรงทุกตัวอักษร):")
        for r in exact:
            print(f"   • {r['ingredient']}")
            print(f"     └─ {r['reason']}")
    
    # แสดงสารที่ AI ยืนยัน
    if confirmed:
        print("\n🔴 สารที่แพ้จริง (AI ยืนยัน):")
        for r in confirmed:
            print(f"   • {r['ingredient']}")
            print(f"     └─ {r['reason']}")
            print(f"     └─ ความเสี่ยง: {r['level']}")
    
    # แสดงสารที่อาจแพ้ไขว้
    if cross:
        print("\n🟡 สารที่อาจแพ้ไขว้:")
        for r in cross:
            print(f"   • {r['ingredient']}")
            print(f"     └─ {r['reason']}")
    
    # แสดงสารที่ไม่เกี่ยวข้อง (ข้อมูลเสริม)
    if false_pos:
        print("\n🟢 สารที่ตรวจพบแต่ไม่เกี่ยวข้อง:")
        for r in false_pos:
            print(f"   • {r['ingredient']}")
            print(f"     └─ {r['reason']}")
else:
    print("\n✅ ไม่พบสารที่คุณแพ้")

# ========== 3. คำแนะนำจากระบบ ==========
print("\n" + "="*70)
print("💡 คำแนะนำจากระบบ:")
print("="*70)
print(f"   {result['recommendation']}")

print("\n" + "="*70)
print("✨ การวิเคราะห์เสร็จสมบูรณ์")
print("="*70 + "\n")