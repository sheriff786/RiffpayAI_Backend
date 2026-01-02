from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.doctor_little.agent import DoctorLittleAgent

router = APIRouter()
agent = DoctorLittleAgent()

class ConsultRequest(BaseModel):
    patient_id: str
    text: str

@router.post("/consult")
async def consult(req: ConsultRequest):
    result = await agent.run(
        patient_id=req.patient_id,
        text=req.text
    )
    return result


