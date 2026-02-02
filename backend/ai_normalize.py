import subprocess
import json

def normalize_ingredients(ingredient_list):
    ingredients_text = "\n".join(ingredient_list)

    prompt = f"""
You are a data normalization engine.

Input is a list of cosmetic ingredient names from OCR.
Each line is ONE ingredient.

OCR Input:
{ingredients_text}

Rules:
- Process ONE line at a time
- Output MUST be valid JSON array
- Same length as input
- No explanation
- If unsure, corrected = "uncertain"

Output JSON ONLY:
[
  {{
    "original": "",
    "corrected": "",
    "confidence": "High | Medium | Low"
  }}
]
"""

    result = subprocess.run(
        ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )

    output = result.stdout.strip()
    output = output[:output.rfind("]")+1]

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return []
