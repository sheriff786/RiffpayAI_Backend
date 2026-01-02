# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.agents.doctor_little.agent import DoctorLittleAgent

# router = APIRouter()
# agent = DoctorLittleAgent()

# class ConsultRequest(BaseModel):
#     patient_id: str
#     text: str

# @router.post("/consult")
# async def consult(req: ConsultRequest):
#     result = await agent.run(
#         patient_id=req.patient_id,
#         text=req.text
#     )
#     return result

# from fastapi import APIRouter
# from pydantic import BaseModel

# from app.agents.doctor_little.agent import DoctorLittleAgent

# router = APIRouter()
# agent = DoctorLittleAgent()


# class ConsultRequest(BaseModel):
#     patient_id: str
#     text: str


# @router.post("/consult")
# async def consult(req: ConsultRequest):
#     return await agent.process_consultation(
#         patient_id=req.patient_id,
#         text_input=req.text
#     )

#----working code ------------------#

# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.agents.doctor_little.agent import DoctorLittleAgent

# router = APIRouter()
# agent = DoctorLittleAgent()

# class ConsultRequest(BaseModel):
#     patient_id: str
#     text: str

# @router.post("/consult")
# async def consult(req: ConsultRequest):
#     return await agent.process_consultation(
#         patient_id=req.patient_id,
#         text_input=req.text
#     )
    
    
#----coral integration code ends gere ------------------#

from fastapi import APIRouter
from pydantic import BaseModel
from app.coral.integration import CoralOrchestrator

router = APIRouter()
coral = CoralOrchestrator()

class ConsultRequest(BaseModel):
    patient_id: str
    text: str
    

@router.post("/consult")
async def consult(req: ConsultRequest):
    """
    FastAPI delegates ALL logic to CORAL
    """
    result = await coral.handle_consultation(req.text)

    return {
        "status": "success",
        "decision": result["mode"],
        "entities": result["entities"],
        "risk": result["risk"],
        "soap_note": result["note"]
    }

