from ocr_tess_test import ocr_image
from ingredient_extractor import extract_ingredients

if __name__ == "__main__":
    img = r"D:\allerGUARD\sample_images\label.jpg"

    text = ocr_image(img)
    ingredients = extract_ingredients(text)

    print("🧪 ส่วนผสมที่ตรวจพบ:\n")
    for ing in ingredients:
        print("-", ing)
