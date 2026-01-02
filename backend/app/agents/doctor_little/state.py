from typing import TypedDict, Optional, Dict, List, Any
from datetime import datetime

class MedicalConsultationState(TypedDict):
    patient_id: str
    text_input: Optional[str]
    
    transcript: Optional[str]
    medical_entities: Optional[Dict]
    risk_assessment: Optional[Dict]
    structured_note: Optional[Dict]

    processing_start_time: float
    #extra--#
    # messages: List[Any]
    # patient_id: str
    # consultation_type: str
    # template_type: str
    
    # # Input data
    # audio_data: Optional[bytes]
    # image_data: Optional[bytes]
    # text_input: Optional[str]
    
    # # Processing results
    # transcript: Optional[str]
    # image_analysis: Optional[Dict]
    # medical_entities: Optional[Dict]
    # clinical_evidence: Optional[List[Dict]]
    # risk_assessment: Optional[Dict]
    # structured_note: Optional[Dict]
    
    # # Metadata
    # processing_start_time: float
    # confidence_scores: Dict[str, float]
    # agent_metrics: Dict[str, Any]