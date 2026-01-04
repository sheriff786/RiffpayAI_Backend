import json
from typing import Dict
from langchain_openai import ChatOpenAI
from .prompts import TRIAGE_PROMPT

class TriageAgent:
    """
    LLM-driven clinical triage agent with safety fallback.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def run(self, entities: Dict, risk: Dict) -> Dict:
        try:
            prompt = TRIAGE_PROMPT.format(
                chief_complaint=entities.get("chief_complaint"),
                symptoms=entities.get("symptoms"),
                red_flags=entities.get("red_flags"),
                risk_score=risk.get("risk_score"),
                urgency_level=risk.get("urgency_level")
            )

            response = await self.llm.ainvoke(prompt)
            raw = response.content.strip()

            return json.loads(raw)

        except Exception:
            # 🔒 SAFETY FALLBACK
            return self._fallback(risk)

    def _fallback(self, risk: Dict) -> Dict:
        urgency = risk.get("urgency_level", "low")

        mapping = {
            "critical": "emergency",
            "high": "urgent",
            "medium": "routine",
            "low": "self_care"
        }

        consultation_type = mapping.get(urgency, "self_care")

        return {
            "consultation_type": consultation_type,
            "recommended_action": "Clinical evaluation recommended",
            "escalation_required": consultation_type in ["emergency", "urgent"],
            "confidence": 0.6
        }
