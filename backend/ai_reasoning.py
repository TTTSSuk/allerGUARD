import subprocess
import json

def analyze_ingredients(normalized_ingredients, user_allergies):
    prompt = f"""
You are an expert in cosmetic ingredient allergy analysis.

Normalized ingredients (JSON):
{json.dumps(normalized_ingredients, ensure_ascii=False)}

User allergies:
{", ".join(user_allergies)}

Task:
- Identify risky ingredients
- Explain why
- Assign risk level

Return JSON ONLY:
{{
  "risky_ingredients": [
    {{
      "name": "",
      "reason": "",
      "risk_level": "Low | Medium | High"
    }}
  ],
  "summary": ""
}}
"""

    result = subprocess.run(
        ["ollama", "run", "scb10x/llama3.1-typhoon2-8b-instruct"],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )

    output = result.stdout.strip()
    output = output[:output.rfind("}")+1]

    return json.loads(output)
