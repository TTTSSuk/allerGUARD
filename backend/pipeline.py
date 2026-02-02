from ingredient_extractor import extract_ingredients
from ai_normalize import normalize_ingredients
from ai_reasoning import analyze_ingredients
from ocr_tess_test import ocr_image
import json

def run_pipeline(image_path, user_allergies):
    # 1. OCR
    ocr_text = ocr_image(image_path)

    # 2. Extract
    raw_ingredients = extract_ingredients(ocr_text)

    if not raw_ingredients:
        return {
            "ingredients": [],
            "analysis": [],
            "error": "No ingredients detected"
        }

    # 3. Normalize
    normalized_raw = normalize_ingredients(raw_ingredients)

    # 🔒 บังคับให้เป็น JSON
    if isinstance(normalized_raw, str):
        try:
            normalized = json.loads(normalized_raw)
        except Exception:
            normalized = []
    else:
        normalized = normalized_raw

    # 4. Reasoning
    analysis = analyze_ingredients(normalized, user_allergies)

    return {
        "ingredients": normalized,
        "analysis": analysis
    }
