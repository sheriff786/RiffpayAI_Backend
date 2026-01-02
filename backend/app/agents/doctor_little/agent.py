from datetime import datetime
from typing import Dict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from .state import MedicalConsultationState


class DoctorLittleAgent:

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        self.workflow = self._build_workflow()

    # ---------- CORE LOGIC ----------

    async def extract_entities(self, text: str) -> Dict:
        prompt = f"""
        Extract medical entities from text and return JSON:
        Text: {text}
        """
        print("chat gpt is triggeresd")
        resp = await self.llm.ainvoke(prompt)
        print("chat response is ",resp)
        return {"raw": resp.content}

    async def assess_risk(self, entities: Dict) -> Dict:
        return {
            "risk_level": "medium",
            "confidence": 0.8
        }

    async def generate_soap(self, entities: Dict, risk: Dict) -> Dict:
        return {
            "SOAP": f"Assessment based on {entities}"
        }

    # ---------- LANGGRAPH ----------

    def _build_workflow(self):
        graph = StateGraph(MedicalConsultationState)

        graph.add_node("entity", self._entity_node)
        graph.add_node("risk", self._risk_node)
        graph.add_node("soap", self._soap_node)

        graph.add_edge(START, "entity")
        graph.add_edge("entity", "risk")
        graph.add_edge("risk", "soap")
        graph.add_edge("soap", END)

        return graph.compile()

    async def _entity_node(self, state):
        state["medical_entities"] = await self.extract_entities(state["text_input"])
        return state

    async def _risk_node(self, state):
        state["risk_assessment"] = await self.assess_risk(state["medical_entities"])
        return state

    async def _soap_node(self, state):
        state["structured_note"] = await self.generate_soap(
            state["medical_entities"],
            state["risk_assessment"]
        )
        return state

    # ---------- PUBLIC ENTRY ----------

    async def run(self, patient_id: str, text: str):
        state = {
            "patient_id": patient_id,
            "text_input": text,
            "processing_start_time": datetime.now().timestamp()
        }
        return await self.workflow.ainvoke(state)
