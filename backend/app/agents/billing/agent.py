import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from .prompts import BILLING_PROMPT

class BillingAgent:
    """
    LLM-guided medical billing agent with deterministic fallback.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def run(
        self,
        triage: Dict,
        risk: Dict,
        icd10_suggestions: List[Dict]
    ) -> Dict:
        try:
            icd_codes = [c["code"] for c in icd10_suggestions]

            prompt = BILLING_PROMPT.format(
                triage_decision=triage.get("decision"),
                risk_score=risk.get("risk_score"),
                icd_codes=icd_codes
            )

            response = await self.llm.ainvoke(prompt)
            raw = response.content.strip()

            return json.loads(raw)

        except Exception:
            return self._fallback(triage, risk)

    def _fallback(self, triage: Dict, risk: Dict) -> Dict:
        """
        Safe deterministic fallback (NO LLM)
        """
        decision = triage.get("decision", "self_care")
        score = risk.get("risk_score", 0)

        if decision == "emergency" or score >= 7:
            level = "high"
            cost = "$1500 – $5000"
        elif decision == "urgent" or score >= 4:
            level = "medium"
            cost = "$500 – $1500"
        else:
            level = "low"
            cost = "$100 – $500"

        return {
            "billable": decision != "self_care",
            "billing_level": level,
            "billing_reason": "Derived from triage and risk level",
            "estimated_cost_range": cost,
            "confidence": 0.6
        }
