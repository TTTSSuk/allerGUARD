from pipeline import run_pipeline

image_path = "D:\\allerGUARD\\sample_images\\label9.jpg"

# ทดสอบโดยระบุสิ่งที่แพ้
print("\n" + "="*70)
print("🛡️  AllerGUARD - ระบบตรวจสารแพ้ในเครื่องสำอาง")
print("="*70)

print("\n📸 กำลังวิเคราะห์ผลิตภัณฑ์...")
print(f"🔍 สิ่งที่ต้องระวัง: curcuma, milk, salicylic acid\n")

result = run_pipeline(image_path, user_allergies=["curcuma", "milk", "salicylic acid"])

print("\n" + "="*70)
print("📋 ส่วนผสมทั้งหมดที่ตรวจพบ ({} รายการ)".format(len(result["cleaned_ingredients"])))
print("="*70)
for idx, ing in enumerate(result["cleaned_ingredients"], 1):
    print(f"{idx:2d}. {ing}")

print("\n" + "="*70)

if result["detected_allergens"]:
    print(f"⚠️  พบสารที่อาจทำให้แพ้ ({len(result['detected_allergens'])} รายการ)")
    print("="*70)
    
    # แยกตาม source
    substring_items = [r for r in result["detected_allergens"] if r.get("source") == "substring"]
    ai_items = [r for r in result["detected_allergens"] if r.get("source") == "ai"]
    
    if substring_items:
        print("\n🔍 ตรวจพบโดยการค้นหาชื่อโดยตรง:")
        for r in substring_items:
            risk_emoji = "🔴" if r['level'].upper() == "HIGH" else "🟡" if r['level'].upper() == "MEDIUM" else "🟢"
            print(f"\n  {risk_emoji} {r['ingredient']}")
            print(f"     → {r['reason']}")
            print(f"     → ระดับความเสี่ยง: {r['level']}")
    
    if ai_items:
        print("\n🤖 ตรวจพบโดย AI (สารในกลุ่มเดียวกัน):")
        for r in ai_items:
            risk_emoji = "🔴" if r['level'].upper() == "HIGH" else "🟡" if r['level'].upper() == "MEDIUM" else "🟢"
            print(f"\n  {risk_emoji} {r['ingredient']}")
            print(f"     → {r['reason']}")
            print(f"     → ระดับความเสี่ยง: {r['level']}")
else:
    print("✅ ไม่พบสารที่คุณแพ้")
    print("="*70)

print("\n" + "="*70)
print("💡 คำแนะนำจากระบบ:")
print("="*70)
print(f"   {result['recommendation']}")

# แสดง AI Analysis
if result.get("ai_analysis"):
    print("\n" + "="*70)
    print("🤖 คำแนะนำโดยละเอียดจาก AI:")
    print("="*70)
    
    # แยกส่วน "คำแนะนำ" ออกมา
    ai_text = result["ai_analysis"]
    
    if "คำแนะนำ:" in ai_text:
        parts = ai_text.split("คำแนะนำ:")
        if len(parts) > 1:
            advice = parts[1].strip()
            print(f"\n{advice}")
    else:
        # แสดงทั้งหมดถ้าไม่มีส่วน "คำแนะนำ"
        print(f"\n{ai_text}")

print("\n" + "="*70)
print("✨ การวิเคราะห์เสร็จสมบูรณ์")
print("="*70 + "\n")