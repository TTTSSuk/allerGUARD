import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("❌ ไม่พบไฟล์ภาพ หรือ path ผิด")
    
    # --- เพิ่มส่วนนี้ ---
    # ขยายภาพเป็น 2 เท่าเพื่อให้ Tesseract อ่านตัวอักษรเล็กๆ ได้ชัดขึ้น
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # ------------------

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    gray = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    custom_config = r'--oem 3 --psm 4'

    text = pytesseract.image_to_string(
        gray,
        lang="eng+tha",
        config=custom_config
    )
    return text.strip()


if __name__ == "__main__":
    img = r"D:\allerGUARD\sample_images\label.jpg"
    text = ocr_image(img)

    print("===== OCR RESULT =====\n")
    print(text)
