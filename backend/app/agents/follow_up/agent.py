import json
from typing import Dict
from langchain_openai import ChatOpenAI
from .prompts import FOLLOW_UP_PROMPT

class FollowUpAgent:
    """
    Patient-facing follow-up communication agent.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    async def run(
        self,
        entities: Dict,
        risk: Dict,
        soap_note: Dict
    ) -> Dict:
        try:
            prompt = FOLLOW_UP_PROMPT.format(
                chief_complaint=entities.get("chief_complaint"),
                urgency=risk.get("urgency_level"),
                risk_score=risk.get("risk_score"),
                plan=soap_note["sections"].get("plan")
            )

            response = await self.llm.ainvoke(prompt)
            raw = response.content.strip()

            return json.loads(raw)

        except Exception:
            return self._fallback(risk)

    def _fallback(self, risk: Dict) -> Dict:
        """
        Deterministic fallback (NO LLM)
        """
        urgency = risk.get("urgency_level", "low")

        if urgency in ["high", "critical"]:
            message = (
                "Your symptoms may be serious. Please seek medical care immediately."
            )
            follow_up = "Immediately"
            seek_help = [
                "worsening pain",
                "shortness of breath",
                "dizziness or collapse"
            ]
        else:
            message = (
                "Your symptoms appear stable at this time. Please monitor how you feel "
                "and follow the recommended plan."
            )
            follow_up = "Within 24–48 hours"
            seek_help = [
                "pain becomes severe",
                "new symptoms develop"
            ]

        return {
            "message": message,
            "follow_up_timing": follow_up,
            "seek_help_if": seek_help,
            "confidence": 0.6
        }
