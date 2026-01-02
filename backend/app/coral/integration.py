# app/coral/integration.py

from app.agents.doctor_little.agent import DoctorLittleAgent

class CoralRouter:
    def __init__(self):
        self.agents = {
            "doctor-little": DoctorLittleAgent()
        }

    async def route(self, request: dict):
        """
        Decide which agent to call
        """
        intent = request.get("intent", "medical")

        if intent == "medical":
            return await self.agents["doctor-little"].process_consultation(
                patient_id=request["patient_id"],
                text_input=request["text"]
            )

        raise ValueError("No agent found for request")
