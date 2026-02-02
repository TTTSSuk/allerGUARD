import easyocr

def ocr_image(image_path):
    reader = easyocr.Reader(['en', 'th'])
    result = reader.readtext(image_path)

    texts = []
    for r in result:
        texts.append(r[1])  # เอาเฉพาะข้อความ

    full_text = "\n".join(texts)
    return full_text


if __name__ == "__main__":
    img = "../sample_images/label2.jpg"  # หรือ path รูปของคุณ
    text = ocr_image(img)

    print("ข้อความที่อ่านได้จากฉลาก:\n")
    print(text)
