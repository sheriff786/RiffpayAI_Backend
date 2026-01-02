# import asyncio
# from app.agents.doctor_little.agent import DoctorLittleAgent
from dotenv import load_dotenv
import os
# from app.agents.doctor_little.agent import DoctorLittleAgent

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
# import os
import asyncio
from app.agents.doctor_little.agent import DoctorLittleAgent

# import asyncio
# from app.agents.doctor_little.agent import DoctorLittleAgent

async def test():
    agent = DoctorLittleAgent()
    result = await agent.run(
        patient_id="P001",
        text="I have chest pain and sweating"
    )
    print(result)

asyncio.run(test())

