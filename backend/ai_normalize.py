import subprocess
import json
from unittest import result

def normalize_ingredients(ingredient_list):
    """
    รับ list ของ ingredient ที่อาจสะกดผิด
    ส่งให้ AI ช่วยแก้ชื่อสารให้เป็นมาตรฐาน
    """
    print("DEBUG input list:", ingredient_list)

    ingredients_text = "\n".join(ingredient_list)
    print("DEBUG ingredients_text:\n", ingredients_text)

    prompt = f"""
You are a data normalization engine.

Input is a list of cosmetic ingredient names from OCR.
Each line is ONE ingredient.

OCR Input:
{ingredients_text}

Rules:
- Process ONE line at a time
- Output MUST be valid JSON
- Output array length MUST equal input length
- DO NOT explain
- DO NOT add new items
- DO NOT merge items
- If unsure, set corrected = "uncertain"

Output JSON format ONLY:

[
  {{
    "original": "...",
    "corrected": "...",
    "confidence": "High | Medium | Low"
  }}
]
"""
    
    result = subprocess.run(
    [
        "ollama",
        "run",
        "scb10x/llama3.1-typhoon2-8b-instruct"
    ],
    input=prompt,
    text=True,
    capture_output=True,
    encoding="utf-8"
)
    print("STDERR:\n", result.stderr)

    output = result.stdout.strip()
    print("RAW AI OUTPUT:\n", output)

    if "]" in output:
        output = output[: output.rfind("]") + 1]

    try:
        json.loads(output)
    except json.JSONDecodeError:
        print("❌ AI output is not valid JSON")
        print(output)

    return output

if __name__ == "__main__":
    test_ingredients = [
        "SalicyIic Acid",
        "Glycerln",
        "PhenoxyethanoI"
    ]

    output = normalize_ingredients(test_ingredients)
    print(output)
