# pipeline_test.py

from pipeline import run_pipeline

image_path = "D:\\allerGUARD\\sample_images\\label.jpg"

result = run_pipeline(image_path)

print("\n🧪 Ingredients detected:")
for ing in result["ingredients"]:
    print(f"- {ing}")

if result["risks"]:
    print("\n⚠️ Potential risks:")
    for r in result["risks"]:
        print(f"- {r['ingredient']} → {r['risk']}")
else:
    print("\n✅ No major risks detected")


# from ocr_tess_test import ocr_image
# from ingredient_extractor import extract_ingredients
# from allergen_checker import check_allergens

# image_path = "D:\\allerGUARD\\sample_images\\label.jpg"

# # 1️⃣ OCR
# ocr_text = ocr_image(image_path)

# # 2️⃣ Extract ingredients
# ingredients = extract_ingredients(ocr_text)

# print("\n🧪 Ingredients detected:")
# for ing in ingredients:
#     print("-", ing)

# # 3️⃣ AI Check allergens
# alerts = check_allergens(ingredients)

# print("\n⚠️ Potential risks:")
# if not alerts:
#     print("✔ No known allergens detected")
# else:
#     for a in alerts:
#         print(f"- {a['ingredient']} → {a['risk']}")
