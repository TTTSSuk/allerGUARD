def summarize_risk(risks):
    if not risks:
        return "LOW"

    levels = [r["risk"]["level"] for r in risks]

    if "high" in levels:
        return "HIGH"
    if "medium" in levels:
        return "MEDIUM"
    return "LOW"
