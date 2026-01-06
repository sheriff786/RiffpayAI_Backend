import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langsmith import traceable
from .prompts import TRIAGE_PROMPT
from app.agents.registry import AgentRegistry
import os
from observability.logging.logger import get_logger
from observability.logging.llm_ada import RequestLogger

_logger = RequestLogger(
    get_logger("Triage agent", "agent.log"),
    {}
)

_logger.info("Triage agent loaded")

class TriageAgent:
    """
    LLM-driven clinical triage agent with safety fallback.
    """
    name = "triage"
    priority = 20
    can_override = True

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

    async def triage(self, entities: Dict, risk: Dict) -> Dict:
        try:
            prompt = TRIAGE_PROMPT.format(
                chief_complaint=entities.get("chief_complaint"),
                symptoms=entities.get("symptoms"),
                red_flags=entities.get("red_flags"),
                risk_score=risk.get("risk_score"),
                urgency_level=risk.get("urgency_level")
            )
            llm = self._get_llm()
            llm_logger = RequestLogger(
            get_logger("llm", "llm.log"),
                {}
            )
            llm_logger.info("LLM CALL: follow up generation")
            response = await llm.ainvoke(prompt)
            llm_logger.info("LLM RETURN")
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
            "confidence": 0.6,
            "fall_back": True
        }
    @traceable(name="TriageAgent",run_type="chain")    
    async def run(self, state: dict) -> dict:
        """
        BaseAgent adapter — does NOT change triage logic
        """

        entities = state.get("entities", {})
        risk = state.get("risk", {})

        triage_result = await self.triage(
            entities=entities,
            risk=risk
        )

        return {
            "triage": triage_result
        }
