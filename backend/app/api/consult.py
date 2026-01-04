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

from unittest import result
from fastapi import APIRouter
from pydantic import BaseModel
from app.coral.integration import CoralOrchestrator
from app.agents.triage.agent import TriageAgent
from app.agents.billing.agent import BillingAgent
from app.agents.follow_up.agent import FollowUpAgent

from app.router.risk_resolver import resolve_final_urgency

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
    triage_agent = TriageAgent()
    billing_agent = BillingAgent()
    follow_up_agent = FollowUpAgent()
    
    #traiage agent
    triage = await triage_agent.run(
    entities=result["entities"],
    risk=result["risk"]
    )
    risk = resolve_final_urgency(result['risk'], triage)
    result["risk"] = risk
    result["triage"] = triage
    #billing agents
    billing = await billing_agent.run(
    triage=result["triage"],
    risk=result["risk"],
    icd10_suggestions=result["note"]["icd10_suggestions"],
    )
    result["billing"] = billing
    #follow up agent
    follow_up = await follow_up_agent.run(
    entities=result["entities"],
    risk=result["risk"],
    soap_note=result["note"]
    )

    result["follow_up"] = follow_up

    
    return {
        "status": "success",
        "consultant_decision": result["mode"],
        "entities": result["entities"],
        "risk": result["risk"],
        "soap_note": result["note"],
        "triage": triage,
        "billing": billing,
        "follow_up": follow_up
    }

