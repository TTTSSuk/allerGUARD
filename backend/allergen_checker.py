from allergen_db import ALLERGEN_DB

def check_allergens(ingredients):
    alerts = []

    for ing in ingredients:
        if ing in ALLERGEN_DB:
            alerts.append({
                "ingredient": ing,
                "risk": ALLERGEN_DB[ing]
            })

    return alerts
