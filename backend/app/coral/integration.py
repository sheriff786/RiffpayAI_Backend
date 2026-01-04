# app/coral/integration.py

# from app.agents.doctor_little.agent import DoctorLittleAgent

# class CoralRouter:
#     def __init__(self):
#         self.agents = {
#             "doctor-little": DoctorLittleAgent()
#         }

#     async def route(self, request: dict):
#         """
#         Decide which agent to call
#         """
#         intent = request.get("intent", "medical")

#         if intent == "medical":
#             return await self.agents["doctor-little"].process_consultation(
#                 patient_id=request["patient_id"],
#                 text_input=request["text"]
#             )

#         raise ValueError("No agent found for request")

# app/coral/integration.py

from typing import Dict
from app.agents.doctor_little.agent import DoctorLittleAgent

class CoralOrchestrator:
    def __init__(self):
        self.agent = DoctorLittleAgent()

    async def handle_consultation(self, text: str) -> Dict:
        """
        CORAL decides:
        - what tools to call
        - in what order
        """

        # 1️⃣ Entity Extraction
        entities = await self.agent.extract_medical_entities_internal(text)

        # 2️⃣ Risk Evaluation
        risk = await self.agent.assess_clinical_risk_internal(
            entities=entities,
            evidence={"results": []}
        )

        # 3️⃣ Escalation Logic (CORAL Brain)
        if risk["urgency_level"] in ["high", "critical"]:
            mode = "emergency"
        else:
            mode = "general"

        # 4️⃣ Documentation
        note = await self.agent.generate_clinical_documentation_internal(
            entities=entities,
            risk_assessment=risk,
            template_type="SOAP"
        )
        

        return {
            "mode": mode,
            "entities": entities,
            "risk": risk,
            "note": note
        }
        
        

