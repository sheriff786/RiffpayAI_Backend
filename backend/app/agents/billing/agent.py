import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langsmith import traceable
from .prompts import BILLING_PROMPT
import os
from app.agents.registry import AgentRegistry
from observability.logging.logger import get_logger
from observability.logging.llm_ada import RequestLogger

_logger = RequestLogger(
    get_logger("Billing agent", "agent.log"),
    {}
)

_logger.info("Billing agent loaded")

class BillingAgent:
    """
    LLM-guided medical billing agent with deterministic fallback.
    
    """
    name = "billing"
    priority = 30
    can_override = False

    def __init__(self):
        AgentRegistry().register(self)
        self.llm = None   # 🔥 DO NOT initialize here

    def _get_llm(self):
        if self.llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set")

            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=api_key
            )
        return self.llm

    async def generate_billing(
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
            llm = self._get_llm()
            llm_logger = RequestLogger(
            get_logger("llm", "llm.log"),
                {}
            )
            llm_logger.info("LLM CALL: billing generation")
            response = await llm.ainvoke(prompt)
            llm_logger.info("LLM RETURN")
            raw = response.content.strip()

            return json.loads(raw)

        except Exception as e:
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
            "confidence": 0.6,
            "fall_back": True
        }
    @traceable(name="BillingAgent",run_type="chain")
    async def run(self, state: dict) -> dict:
        """
        BaseAgent adapter — billing only
        """

        billing = await self.generate_billing(
            triage=state.get("triage", {}),
            risk=state.get("risk", {}),
            icd10_suggestions=state.get("note", {}).get("icd10_suggestions", [])
        )

        return {
            "billing": billing
        }
