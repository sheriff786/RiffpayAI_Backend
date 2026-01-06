# from ast import List
import base64
from datetime import datetime
import re
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
import os

from app.agents.registry import AgentRegistry
from .state import MedicalConsultationState
from .state import MedicalConsultationState, UrgencyLevel
from .workflow import build_workflow
from .tools import DoctorLittleTools
from . import prompts
import json


from datetime import datetime
from typing import Dict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from .state import MedicalConsultationState
from app.agents.base import BaseAgent

from observability.logging.logger import get_logger
from observability.logging.llm_ada import RequestLogger

_logger = RequestLogger(
    get_logger("doctor_little", "agent.log"),
    {}
)

_logger.info("Entering entity extraction")


class DoctorLittleAgent(BaseAgent):
    name = "doctor-little"
    priority = 10          # runs first
    can_override = False


    def __init__(self):
        AgentRegistry().register(self)
        self.tools = DoctorLittleTools(self)
        self.workflow = build_workflow(self)
        self.llm = None
        self._llm_model = "gpt-4o-mini"
        self._llm_temperature = 0
        self.templates = {
            "SOAP": {
                "name": "SOAP Note",
                "sections": ["subjective", "objective", "assessment", "plan"]
            }
        }
        self.agent_id = "doctor-little-medical-agent"
        self.agent_version = "2.0.0"
        self._llm_used = False
        self._llm_cache = None
        
    def _get_llm(self):
        if self.llm is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is required when invoking LLM tools"
                )

            self.llm = ChatOpenAI(
                model=self._llm_model,
                temperature=self._llm_temperature,
                api_key=api_key
            )
        return self.llm
    # def _get_llm(self):
    #     if self._llm is None:
    #         self._llm = ChatOpenAI(
    #             model="gpt-4o-mini",
    #             temperature=0,
    #             api_key=os.getenv("OPENAI_API_KEY"),
    #         )
    #     return self._llm



    async def _voice_processing_node(self, state: MedicalConsultationState):
        if state.get("audio_data"):
            audio_b64 = base64.b64encode(state["audio_data"]).decode()
            result = await self.process_voice_consultation_internal(
                audio_b64, state["patient_id"]
            )
            state["transcript"] = result.get("transcript")
            state["confidence_scores"]["voice"] = result.get("confidence", 0.0)

        elif state.get("text_input"):
            state["transcript"] = state["text_input"]
            state["confidence_scores"]["voice"] = 1.0

        return state



    async def _image_analysis_node(self, state):
        if state.get("image_data"):
            image_b64 = base64.b64encode(state["image_data"]).decode()
            result = await self.analyze_medical_image_internal(image_b64)
            state["image_analysis"] = result.get("analysis")
            state["confidence_scores"]["image"] = result.get("confidence", 0.0)

        return state


    # async def _entity_extraction_node(self, state):
    #     if state.get("medical_entities"):
    #         return state 
    #     if state.get("transcript"):
    #         result = await self.extract_medical_entities_internal(state["transcript"])
    #         state["medical_entities"] = result
    #         state["confidence_scores"]["entities"] = result.get(
    #             "extraction_confidence", 0.0
    #         )

    #     return state
    
    #providing fix 
    async def _entity_extraction_node(self, state):
        # 🚫 HARD STOP: already ran once
        if state.get("_llm_result"):
            state["medical_entities"] = state["_llm_result"]
            return state

        if not state.get("transcript"):
            return state

        llm = self._get_llm()
        prompt = prompts.ENTITY_EXTRACTION_PROMPT.format(
            text=state["transcript"]
        )
        #logger info
        llm_logger = RequestLogger(
            get_logger("llm", "llm.log"),
            {}
        )
        llm_logger.info("LLM CALL: ENTITY_EXTRACTION")
        response = await llm.ainvoke(prompt)
        llm_logger.info("LLM RETURN")
        raw_entities = self._extract_json_from_llm(response.content)
        entities = self._canonicalize_entities(raw_entities)

        # 🔐 CACHE RESULT (THIS IS THE KEY)
        state["_llm_result"] = entities
        state["medical_entities"] = entities
        state["confidence_scores"]["entities"] = 0.9

        return state


    # async def _evidence_search_node(self, state):
    #     if state.get("medical_entities"):
    #         query_parts = []

    #         if state["medical_entities"].get("chief_complaint"):
    #             query_parts.append(state["medical_entities"]["chief_complaint"])

    #         symptoms = state["medical_entities"].get("symptoms", [])
    #         if isinstance(symptoms, list):
    #             query_parts.extend(symptoms[:3])

    #         query = " ".join(query_parts)

    #         if query:
    #             result = await self.search_clinical_evidence_internal(query)
    #             state["clinical_evidence"] = result.get("results", [])

    #     return state
    async def _evidence_search_node(self, state):
        entities = state.get("medical_entities") or {}
        query_parts = []

        cc = entities.get("chief_complaint")
        if isinstance(cc, str):
            query_parts.append(cc)

        symptoms = entities.get("symptoms", [])
        if isinstance(symptoms, list):
            query_parts.extend([s for s in symptoms if isinstance(s, str)])

        query = " ".join(query_parts)

        if query:
            result = await self.search_clinical_evidence_internal(query)
            state["clinical_evidence"] = result.get("results", [])

        return state



    async def _risk_assessment_node(self, state):
        if state.get("medical_entities"):
            evidence = {"results": state.get("clinical_evidence", [])}
            result = await self.assess_clinical_risk_internal(
                state["medical_entities"], evidence
            )
            state["risk_assessment"] = result
            state["confidence_scores"]["risk"] = result.get("confidence", 0.0)

        return state


    async def _documentation_node(self, state):
        if state.get("medical_entities") and state.get("risk_assessment"):
            result = await self.generate_clinical_documentation_internal(
                state["medical_entities"],
                state["risk_assessment"],
                state["template_type"],
            )
            state["structured_note"] = result

        return state


    async def _quality_check_node(self, state: MedicalConsultationState):
        processing_time = datetime.now().timestamp() - state["processing_start_time"]

        confidences = list(state["confidence_scores"].values())

        state["agent_metrics"] = {
            "total_processing_time": round(processing_time, 2),
            "average_confidence": round(
                sum(confidences) / len(confidences), 2
            ) if confidences else 0.0,
            "components_processed": len(
                [c for c in confidences if c > 0]
            ),
            "has_voice": bool(state.get("transcript")),
            "has_image": bool(state.get("image_analysis")),
            "risk_level": state.get("risk_assessment", {}).get("urgency_level"),
            "documentation_quality": state.get("structured_note", {})
                .get("quality_metrics", {})
                .get("overall_score", 0),
        }

        return state

    async def generate_clinical_documentation_internal(self, 
                                            entities: Dict, 
                                            risk_assessment: Dict, 
                                            template_type: str = "SOAP") -> Dict:
        """
        Internal method for documentation generation (non-tool version)
        """
        try:
            template = self.templates.get(template_type, self.templates["SOAP"])
            
            # Generate sections based on template
            sections = {}
            for section in template["sections"]:
                sections[section] = self._generate_section(section, entities, risk_assessment)
            
            # Create formatted note
            formatted_text = self._format_clinical_note(sections, template["name"])
            
            # Calculate quality metrics
            quality_metrics = self._calculate_documentation_quality(sections, entities)
            
            # Generate ICD-10 suggestions
            icd10_suggestions = self._suggest_icd10_codes(entities)
            
            return {
                "template_type": template_type,
                "template_name": template["name"],
                "sections": sections,
                "formatted_text": formatted_text,
                "quality_metrics": quality_metrics,
                "icd10_suggestions": icd10_suggestions,
                "word_count": len(formatted_text.split()),
                "generated_at": datetime.now().isoformat(),
                "agent_version": self.agent_version
            }
            
        except Exception as e:
            return {
                "error": f"Documentation generation failed: {str(e)}",
                "template_type": template_type,
                "sections": {}
            }

   
    import json
    import re
    import json

    def _extract_json_from_llm(self, text: str) -> dict:
        """
        Safely extracts the first JSON object from an LLM response.
        Handles markdown, explanations, and extra text.
        """

        # Try fenced ```json block first
        fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            return json.loads(fence_match.group(1))

        # Fallback: first {...} block
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            return json.loads(brace_match.group(1))

        raise ValueError("No valid JSON found in LLM response")
    
    # def _normalize_entities(self, entities: dict) -> dict:
    #     """
    #     Converts LLM structured output into internal flat schema.
    #     """

    #     def unwrap(field):
    #         if isinstance(field, dict) and "value" in field:
    #             return field["value"]
    #         return field

    #     normalized = {}

    #     for key, value in entities.items():
    #         normalized[key] = unwrap(value)

    #     # Fix pain assessment naming
    #     pain = normalized.get("pain_assessment", {})
    #     if isinstance(pain, dict):
    #         if "intensity" in pain:
    #             pain["severity"] = pain.pop("intensity")

    #     return normalized
    def _canonicalize_entities(self, raw: dict) -> dict:
        """
        Convert LLM entity output into strict internal schema.
        Ensures downstream safety.
        """

        def unwrap(v):
            if isinstance(v, dict) and "value" in v:
                return v["value"]
            return v

        entities = {}

        # -------- Scalars --------
        cc = unwrap(raw.get("chief_complaint"))
        entities["chief_complaint"] = cc if isinstance(cc, str) else "not specified"

        entities["timeline"] = unwrap(raw.get("timeline")) or "not specified"

        # -------- Lists --------
        symptoms = unwrap(raw.get("symptoms"))
        if isinstance(symptoms, str):
            symptoms = [symptoms]
        entities["symptoms"] = symptoms if isinstance(symptoms, list) else []

        red_flags = unwrap(raw.get("red_flags"))
        if isinstance(red_flags, str):
            red_flags = [red_flags]
        entities["red_flags"] = red_flags if isinstance(red_flags, list) else []

        # -------- Pain assessment --------
        pain_raw = unwrap(raw.get("pain_assessment"))
        pain = {}

        if isinstance(pain_raw, dict):
            if "intensity" in pain_raw:
                pain["severity"] = int(pain_raw["intensity"])
            elif "severity" in pain_raw:
                pain["severity"] = int(pain_raw["severity"])
            pain["scale"] = pain_raw.get("scale", "out of 10")

        elif isinstance(pain_raw, str):
            import re
            m = re.search(r"(\d+)", pain_raw)
            if m:
                pain["severity"] = int(m.group(1))
                pain["scale"] = "out of 10"

        entities["pain_assessment"] = pain

        # -------- Defaults --------
        for key in [
            "medications", "allergies", "medical_history",
            "vital_signs", "physical_findings",
            "risk_factors", "social_history", "family_history"
        ]:
            entities[key] = unwrap(raw.get(key)) or "not specified"

        # -------- Auto red-flag logic --------
        if isinstance(entities["chief_complaint"], str):
            if "chest pain" in entities["chief_complaint"].lower():
                entities["red_flags"].append("chest pain")

        return entities




    async def extract_medical_entities_internal(self, text: str) -> Dict:
        """
        Uses LLM to extract structured medical entities from clinical text.
        Cleans markdown JSON safely.
        """

        prompt = prompts.ENTITY_EXTRACTION_PROMPT.format(text=text)

        llm = self._get_llm()
        response = await llm.ainvoke(prompt)


        # raw = response.content.strip()

        # # 🔥 FIX: CLEAN ```json ``` BLOCKS
        # if raw.startswith("```"):
        #     raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            raw_entities = self._extract_json_from_llm(response.content)
            entities = self._canonicalize_entities(raw_entities)
        except Exception:
            entities = self._canonicalize_entities(
            self._fallback_entity_extraction(text)
            )
                    # entities = {
            #     "chief_complaint": "not specified",
            #     "symptoms": [],
            #     "pain_assessment": {},
            # }

        entities.update({
            "extraction_confidence": 0.9,
            "processing_time": datetime.now().timestamp(),
            "text_length": len(text),
            "entities_found": len(
                [v for v in entities.values() if v not in ("not specified", [], {}, None)]
            )
        })

        return entities
    async def search_clinical_evidence_internal(self, query: str, max_results: int = 5) -> Dict:
        """
        Internal method for evidence search (non-tool version)
        """
        try:
            query_lower = query.lower()
            relevant_guidelines = []
            medical_guidelines = self._load_medical_guidelines()
            # Search through loaded guidelines
            for guideline in medical_guidelines:
                relevance_score = 0.0
                
                # Check title relevance
                if any(keyword in query_lower for keyword in guideline["keywords"]):
                    relevance_score += 0.8
                
                # Check red flags
                if any(flag in query_lower for flag in guideline.get("red_flags", [])):
                    relevance_score += 0.9
                
                # Check category relevance
                if guideline["category"] in query_lower:
                    relevance_score += 0.6
                
                if relevance_score > 0.3:
                    relevant_guidelines.append({
                        **guideline,
                        "relevance_score": relevance_score
                    })
            
            # Sort by relevance and limit results
            relevant_guidelines.sort(key=lambda x: x["relevance_score"], reverse=True)
            relevant_guidelines = relevant_guidelines[:max_results]
            
            return {
                "query": query,
                "results": relevant_guidelines,
                "total_found": len(relevant_guidelines),
                "search_time": datetime.now().timestamp()
            }
            
        except Exception as e:
            return {
                "error": f"Evidence search failed: {str(e)}",
                "results": []
            }
            
    async def assess_clinical_risk_internal(self, entities: Dict, evidence: Dict) -> Dict:
        """
        Internal method for risk assessment (non-tool version)
        """
        try:
            # Initialize risk factors
            risk_factors = {
                "red_flags": 0,
                "pain_severity": 0,
                "vital_signs": 0,
                "symptom_complexity": 0,
                "chronic_conditions": 0
            }
            
            # Assess red flags
            red_flags = entities.get("red_flags", [])
            if isinstance(red_flags, list):
               risk_factors["red_flags"] = len(red_flags) * 2

            
            # Assess pain severity
            pain_info = entities.get("pain_assessment", {})
            if isinstance(pain_info, dict):
                severity = pain_info.get("severity", 0)
                if isinstance(severity, (int, float)):
                    risk_factors["pain_severity"] = min(severity, 10)
            
            # Assess symptom complexity
            symptoms = entities.get("symptoms", [])
            if isinstance(symptoms, list):
                risk_factors["symptom_complexity"] = min(len(symptoms), 10)
            
            # Calculate overall risk score (0-10)
            weights = {
                "red_flags": 0.4,
                "pain_severity": 0.2,
                "vital_signs": 0.2,
                "symptom_complexity": 0.1,
                "chronic_conditions": 0.1
            }
            
            weighted_score = sum(risk_factors[factor] * weights[factor] for factor in weights)
            risk_score = min(weighted_score, 10)
            
            # Determine urgency level
            if risk_score >= 8:
                urgency = UrgencyLevel.CRITICAL
            elif risk_score >= 6:
                urgency = UrgencyLevel.HIGH
            elif risk_score >= 4:
                urgency = UrgencyLevel.MEDIUM
            else:
                urgency = UrgencyLevel.LOW
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(urgency, entities, evidence)
            
            return {
                "risk_score": round(risk_score, 1),
                "urgency_level": urgency.value,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "assessment_time": datetime.now().timestamp(),
                "confidence": 0.85
            }
            
        except Exception as e:
            return {
                "error": f"Risk assessment failed: {str(e)}",
                "risk_score": 5.0,
                "urgency_level": "medium"
            }
            
    def _get_image_analysis_prompt(self, analysis_type: str) -> str:
        """Get appropriate prompt for medical image analysis"""
        base_prompt = """
        You are a medical AI assistant specializing in image analysis. Analyze this medical image and provide:

        1. **Visual Description**: What you observe in the image
        2. **Anatomical Structures**: Identify visible anatomical structures
        3. **Abnormal Findings**: Note any abnormalities, lesions, or concerning features
        4. **Clinical Significance**: Potential clinical implications
        5. **Recommendations**: Suggested follow-up or additional imaging
        6. **Confidence Level**: Your confidence in the analysis (0-100%)

        Important: This is for informational purposes only and should not replace professional medical diagnosis.
        """
        
        if analysis_type == "dermatology":
            return base_prompt + "\nFocus on skin lesions, color changes, texture, and dermatological patterns."
        elif analysis_type == "radiology":
            return base_prompt + "\nFocus on radiological findings, contrast, and anatomical abnormalities."
        else:
            return base_prompt + "\nProvide a general medical assessment of the image."

    def _parse_image_analysis(self, analysis_text: str, analysis_type: str) -> Dict:
        """Parse structured analysis from GPT-4 Vision response"""
        return {
            "raw_analysis": analysis_text,
            "analysis_type": analysis_type,
            "findings": "Parsed findings would go here",
            "recommendations": "Parsed recommendations would go here"
        }

    def _fallback_entity_extraction(self, text: str) -> Dict:
        text_lower = text.lower()

        entities = {
            "chief_complaint": "not specified",
            "symptoms": [],
            "pain_assessment": {},
            "red_flags": [],
            "extraction_confidence": 0.7
        }

        if "chest pain" in text_lower:
            entities["chief_complaint"] = "chest pain"
            entities["symptoms"].append("chest pain")

        import re
        pain_match = re.search(r'(\d+)\s*(out of|/)\s*10', text_lower)
        if pain_match:
            entities["pain_assessment"]["severity"] = int(pain_match.group(1))

        if "left arm" in text_lower:
            entities["pain_assessment"]["radiation"] = "left arm"
            entities["red_flags"].append("pain radiating to left arm")

        return entities


    def _generate_risk_recommendations(self, urgency: UrgencyLevel, entities: Dict, evidence: Dict) -> List[str]:
        """Generate clinical recommendations based on risk level"""
        recommendations = []
        
        if urgency == UrgencyLevel.CRITICAL:
            recommendations.extend([
                "Immediate medical attention required",
                "Consider emergency department evaluation",
                "Vital signs monitoring",
                "Prepare for potential interventions"
            ])
        elif urgency == UrgencyLevel.HIGH:
            recommendations.extend([
                "Urgent medical evaluation within 1 hour",
                "Serial vital signs",
                "Consider diagnostic testing"
            ])
        elif urgency == UrgencyLevel.MEDIUM:
            recommendations.extend([
                "Medical evaluation within 24 hours",
                "Monitor symptoms",
                "Return if symptoms worsen"
            ])
        else:
            recommendations.extend([
                "Routine follow-up as appropriate",
                "Monitor symptoms",
                "Lifestyle modifications as indicated"
            ])
        
        return recommendations

    def _generate_section(self, section: str, entities: Dict, risk_assessment: Dict) -> str:
        """Generate specific documentation section"""
        if section == "subjective":
            return self._generate_subjective_section(entities)
        elif section == "objective":
            return self._generate_objective_section(entities)
        elif section == "assessment":
            return self._generate_assessment_section(entities, risk_assessment)
        elif section == "plan":
            return self._generate_plan_section(risk_assessment)
        elif section == "chief_complaint":
            return entities.get("chief_complaint", "Not specified")
        else:
            return f"[{section.upper()}: To be completed by clinician]"

    def _generate_subjective_section(self, entities: Dict) -> str:
        """Generate SOAP Subjective section"""
        parts = []
        
        if entities.get("chief_complaint"):
            parts.append(f"Chief complaint: {entities['chief_complaint']}")
        
        symptoms = entities.get("symptoms", [])
        if symptoms:
            parts.append(f"Associated symptoms: {', '.join(symptoms)}")
        
        pain = entities.get("pain_assessment", {})
        if isinstance(pain, dict) and pain.get("severity"):
            parts.append(f"Pain severity: {pain['severity']}/10")

        
        return ". ".join(parts) + "." if parts else "Patient history to be obtained."

    def _generate_objective_section(self, entities: Dict) -> str:
        """Generate SOAP Objective section"""
        parts = []
        
        vitals = entities.get("vital_signs", {})
        # if vitals:
        #     vital_strings = [f"{k}: {v}" for k, v in vitals.items()]
        #     parts.append(f"Vital signs: {', '.join(vital_strings)}")
        
        # physical = entities.get("physical_findings", [])
        # if physical:
        #     parts.append(f"Physical exam: {', '.join(physical)}")
        
        # return ". ".join(parts) + "." if parts else "Physical examination to be performed."
        if isinstance(vitals, dict) and vitals:
            vital_strings = [f"{k}: {v}" for k, v in vitals.items()]
            parts.append(f"Vital signs: {', '.join(vital_strings)}")

        physical = entities.get("physical_findings")

        if isinstance(physical, list) and physical:
            parts.append(f"Physical exam: {', '.join(physical)}")

        return ". ".join(parts) + "." if parts else "Physical examination to be performed."

    def _generate_assessment_section(self, entities: Dict, risk_assessment: Dict) -> str:
        """Generate SOAP Assessment section"""
        parts = []
        
        if entities.get("chief_complaint"):
            parts.append(f"Patient presenting with {entities['chief_complaint']}")
        
        if risk_assessment.get("urgency_level"):
            urgency = risk_assessment["urgency_level"]
            risk_score = risk_assessment.get("risk_score", 0)
            parts.append(f"Clinical risk assessment: {urgency} urgency (score: {risk_score}/10)")
        
        return ". ".join(parts) + "." if parts else "Clinical assessment pending."

    def _generate_plan_section(self, risk_assessment: Dict) -> str:
        """Generate SOAP Plan section"""
        recommendations = risk_assessment.get("recommendations", [])
        if recommendations:
            return "Plan: " + "; ".join(recommendations) + "."
        return "Treatment plan to be determined."

    def _format_clinical_note(self, sections: Dict, template_name: str) -> str:
        """Format clinical note as text"""
        lines = [
            f"{template_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            ""
        ]
        
        for section_key, content in sections.items():
            section_name = section_key.replace("_", " ").upper()
            lines.extend([
                f"{section_name}:",
                content,
                ""
            ])
        
        return "\n".join(lines)

    def _calculate_documentation_quality(self, sections: Dict, entities: Dict) -> Dict:
        """Calculate documentation quality metrics"""
        completed_sections = len([s for s in sections.values() if s and not s.startswith("[")])
        total_sections = len(sections)
        
        completeness = (completed_sections / total_sections) * 100 if total_sections > 0 else 0
        
        # Check for key clinical elements
        key_elements = ["chief_complaint", "symptoms", "assessment"]
        elements_present = sum(1 for elem in key_elements if entities.get(elem))
        clinical_accuracy = (elements_present / len(key_elements)) * 100
        
        overall_score = (completeness * 0.6) + (clinical_accuracy * 0.4)
        
        return {
            "completeness": round(completeness, 1),
            "clinical_accuracy": round(clinical_accuracy, 1),
            "overall_score": round(overall_score, 1),
            "completed_sections": completed_sections,
            "total_sections": total_sections
        }

    def _suggest_icd10_codes(self, entities: Dict) -> List[Dict]:
        """Suggest relevant ICD-10 codes based on extracted entities"""
        suggestions = []
        
        symptoms = entities.get("symptoms", [])
        chief_complaint = entities.get("chief_complaint", "").lower()
        icd10_codes=self._load_icd10_codes()
        for code_info in icd10_codes:
            score = 0.0
            
            # Check against chief complaint
            if any(word in chief_complaint for word in code_info["description"].lower().split()):
                score += 0.8
            
            # Check against symptoms
            for symptom in symptoms:
                if isinstance(symptom, str) and any(word in symptom.lower() for word in code_info["description"].lower().split()):
                    score += 0.6
            
            if score > 0.3:
                suggestions.append({
                    **code_info,
                    "confidence": min(score, 1.0),
                    "rationale": f"Matches clinical presentation"
                })
        
        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)[:5]
    
    
    def _load_medical_guidelines(self) -> List[Dict]:
        """Load clinical guidelines and evidence base"""
        return [
            {
                "id": "chest-pain-acs",
                "title": "Acute Coronary Syndrome Guidelines",
                "category": "cardiology",
                "keywords": ["chest pain", "acs", "heart attack", "myocardial infarction"],
                "recommendations": [
                    "Immediate 12-lead ECG within 10 minutes",
                    "Serial cardiac troponins at 0, 3, 6 hours",
                    "Aspirin 325mg immediately unless contraindicated",
                    "HEART score for risk stratification"
                ],
                "red_flags": ["crushing chest pain", "radiation to arm/jaw", "diaphoresis", "nausea"],
                "evidence_level": "A"
            },
            {
                "id": "respiratory-distress",
                "title": "Acute Respiratory Distress Protocol",
                "category": "pulmonology",
                "keywords": ["shortness of breath", "dyspnea", "respiratory failure"],
                "recommendations": [
                    "Pulse oximetry immediately",
                    "Chest X-ray within 30 minutes",
                    "ABG if oxygen saturation <92%",
                    "Consider PE protocol if indicated"
                ],
                "red_flags": ["severe dyspnea", "cyanosis", "altered mental status"],
                "evidence_level": "A"
            }
        ]
    
    def _load_icd10_codes(self) -> List[Dict]:
        """Load ICD-10 diagnostic codes"""
        return [
            {"code": "R06.02", "description": "Shortness of breath", "category": "respiratory"},
            {"code": "R07.89", "description": "Other chest pain", "category": "cardiovascular"},
            {"code": "R51.9", "description": "Headache, unspecified", "category": "neurological"},
            {"code": "R10.9", "description": "Unspecified abdominal pain", "category": "gastrointestinal"},
            {"code": "I20.9", "description": "Angina pectoris, unspecified", "category": "cardiovascular"}
        ]
        
    def _load_clinical_templates(self) -> Dict:
        """Load clinical documentation templates"""
        return {
            "SOAP": {
                "name": "SOAP Note",
                "sections": ["subjective", "objective", "assessment", "plan"],
                "description": "Standard clinical documentation format"
            },
            "H_AND_P": {
                "name": "History & Physical",
                "sections": ["chief_complaint", "hpi", "pmh", "medications", "allergies", 
                           "social_history", "family_history", "ros", "physical_exam", "assessment_plan"],
                "description": "Comprehensive patient assessment"
            },
            "EMERGENCY": {
                "name": "Emergency Assessment",
                "sections": ["chief_complaint", "vital_signs", "primary_survey", "secondary_assessment", 
                           "diagnostics", "treatment", "disposition"],
                "description": "Emergency department documentation"
            }
        }
        
    def get_agent_info(self) -> Dict:
        """Get agent information and capabilities"""
        return {
            "agent_id": self.agent_id,
            "agent_name": "Doctor Little - AI Medical Agent",
            "version": self.agent_version,
            "description": "Comprehensive AI medical agent providing voice transcription, image analysis, clinical reasoning, and documentation generation",
            "capabilities": [
                "voice_processing",
                "medical_image_analysis", 
                "clinical_entity_extraction",
                "evidence_based_medicine",
                "clinical_risk_assessment",
                "structured_documentation"
            ],
            "supported_templates": list(self.templates.keys()),
            "consultation_types": ["general", "emergency", "follow_up"],
            "input_modalities": ["voice", "text", "image"],
            "output_formats": ["SOAP", "H_AND_P", "EMERGENCY"],
            "clinical_specialties": [
                "general_medicine",
                "emergency_medicine", 
                "internal_medicine",
                "family_medicine"
            ]
        }

    # ---------------------------
    # SINGLE ENTRY POINT (LOCKED)
    # ---------------------------
    from langsmith import traceable

    async def process_consultation(
        self,
        patient_id: str,
        text_input: str,
        template_type: str = "SOAP",
        consultation_type: str = "general"
    ) -> Dict:

        initial_state: MedicalConsultationState = {
            "patient_id": patient_id,
            "consultation_type": consultation_type,
            "template_type": template_type,

            "text_input": text_input,
            "audio_data": None,
            "image_data": None,

            "transcript": None,
            "image_analysis": None,
            "medical_entities": None,
            "clinical_evidence": None,
            "risk_assessment": None,
            "structured_note": None,

            "processing_start_time": datetime.now().timestamp(),
            "confidence_scores": {"voice": 0.0,
                        "image": 0.0,
                        "entities": 0.0,
                        "risk": 0.0,},
            "agent_metrics": {"total_processing_time": 0.0,
                        "average_confidence": 0.0,
                        "components_processed": 0
                        },
            "messages": [],
            "agent_version": self.agent_version
        }

        final_state = await self.workflow.ainvoke(initial_state)
        return final_state
        # -------------------------------------------------
    # BaseAgent compatibility adapter (DO NOT CHANGE)
    # -------------------------------------------------
    @traceable(name="DoctorLittleAgent",run_type="chain")
    async def run(self, state: dict) -> dict:
        """
        Adapter method required by BaseAgent.
        This does NOT change internal logic.
        """

        result = await self.process_consultation(
            patient_id=state.get("patient_id", "UNKNOWN"),
            text_input=state.get("text"),
            template_type=state.get("template_type", "SOAP"),
            consultation_type=state.get("consultation_type", "general"),
        )

        # Normalize output for registry / router
        return {
            "mode": result.get("consultation_type", "general"),
            "entities": result.get("medical_entities"),
            "risk": result.get("risk_assessment"),
            "note": result.get("structured_note"),
            "agent_metrics": result.get("agent_metrics"),
        }

