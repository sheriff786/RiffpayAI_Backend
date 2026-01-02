from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
# class MedicalConsultationState(TypedDict):
#     patient_id: str
#     text_input: Optional[str]
    
#     transcript: Optional[str]
#     medical_entities: Optional[Dict]
#     risk_assessment: Optional[Dict]
#     structured_note: Optional[Dict]

#     processing_start_time: float
#     #extra--#
#     # messages: List[Any]
#     # patient_id: str
#     # consultation_type: str
#     # template_type: str
    
#     # # Input data
#     # audio_data: Optional[bytes]
#     # image_data: Optional[bytes]
#     # text_input: Optional[str]
    
#     # # Processing results
#     # transcript: Optional[str]
#     # image_analysis: Optional[Dict]
#     # medical_entities: Optional[Dict]
#     # clinical_evidence: Optional[List[Dict]]
#     # risk_assessment: Optional[Dict]
#     # structured_note: Optional[Dict]
    
#     # # Metadata
#     # processing_start_time: float
#     # confidence_scores: Dict[str, float]
#     # agent_metrics: Dict[str, Any]
    
    
    
from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime


class MedicalConsultationState(TypedDict):
    """
    Central state object passed across LangGraph nodes.
    This is the single source of truth for the Doctor Little agent.
    """

    # -------------------------
    # Core identifiers
    # -------------------------
    patient_id: str
    consultation_type: str          # general | emergency | follow_up
    template_type: str              # SOAP | H_AND_P | EMERGENCY

    # -------------------------
    # Input modalities
    # -------------------------
    text_input: Optional[str]
    audio_data: Optional[bytes]
    image_data: Optional[bytes]

    # -------------------------
    # Intermediate processing
    # -------------------------
    transcript: Optional[str]
    image_analysis: Optional[Dict]
    medical_entities: Optional[Dict]
    clinical_evidence: Optional[List[Dict]]
    risk_assessment: Optional[Dict]

    # -------------------------
    # Final output
    # -------------------------
    structured_note: Optional[Dict]

    # -------------------------
    # Metadata & metrics
    # -------------------------
    processing_start_time: float
    confidence_scores: Dict[str, float]
    agent_metrics: Dict[str, Any]
    messages: List[Any]
    
    
class UrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"