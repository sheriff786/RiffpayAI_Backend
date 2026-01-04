def resolve_final_urgency(risk: dict, triage: dict) -> dict:
    """
    Ensure consistency between clinical risk and triage decision
    """
    if triage.get("decision") == "emergency":
        risk["urgency_level"] = "high"
        risk["risk_score"] = max(risk.get("risk_score", 0), 7.5)
        risk["escalated_by"] = "triage"

    return risk
