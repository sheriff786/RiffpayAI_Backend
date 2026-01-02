import base64
from datetime import datetime
from typing import Dict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from .state import MedicalConsultationState
from .state import MedicalConsultationState, UrgencyLevel
from .workflow import build_workflow
from .tools import DoctorLittleTools
from . import prompts


# class DoctorLittleAgent:

#     def __init__(self):
#         self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

#         self.workflow = self._build_workflow()

#     # ---------- CORE LOGIC ----------

#     async def extract_entities(self, text: str) -> Dict:
#         prompt = f"""
#         Extract medical entities from text and return JSON:
#         Text: {text}
#         """
#         print("chat gpt is triggeresd")
#         resp = await self.llm.ainvoke(prompt)
#         print("chat response is ",resp)
#         return {"raw": resp.content}

#     async def assess_risk(self, entities: Dict) -> Dict:
#         return {
#             "risk_level": "medium",
#             "confidence": 0.8
#         }

#     async def generate_soap(self, entities: Dict, risk: Dict) -> Dict:
#         return {
#             "SOAP": f"Assessment based on {entities}"
#         }

#     # ---------- LANGGRAPH ----------

#     def _build_workflow(self):
#         graph = StateGraph(MedicalConsultationState)

#         graph.add_node("entity", self._entity_node)
#         graph.add_node("risk", self._risk_node)
#         graph.add_node("soap", self._soap_node)

#         graph.add_edge(START, "entity")
#         graph.add_edge("entity", "risk")
#         graph.add_edge("risk", "soap")
#         graph.add_edge("soap", END)

#         return graph.compile()

#     async def _entity_node(self, state):
#         state["medical_entities"] = await self.extract_entities(state["text_input"])
#         return state

#     async def _risk_node(self, state):
#         state["risk_assessment"] = await self.assess_risk(state["medical_entities"])
#         return state

#     async def _soap_node(self, state):
#         state["structured_note"] = await self.generate_soap(
#             state["medical_entities"],
#             state["risk_assessment"]
#         )
#         return state

#     # ---------- PUBLIC ENTRY ----------

#     async def run(self, patient_id: str, text: str):
#         state = {
#             "patient_id": patient_id,
#             "text_input": text,
#             "processing_start_time": datetime.now().timestamp()
#         }
#         return await self.workflow.ainvoke(state)


from datetime import datetime
from typing import Dict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

from .state import MedicalConsultationState



class DoctorLittleAgent:

    def __init__(self):
        self.tools = DoctorLittleTools(self)
        self.workflow = build_workflow(self)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

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


    async def _entity_extraction_node(self, state):
        if state.get("transcript"):
            result = await self.extract_medical_entities_internal(state["transcript"])
            state["medical_entities"] = result
            state["confidence_scores"]["entities"] = result.get(
                "extraction_confidence", 0.0
            )

        return state


    async def _evidence_search_node(self, state):
        if state.get("medical_entities"):
            query_parts = []

            if state["medical_entities"].get("chief_complaint"):
                query_parts.append(state["medical_entities"]["chief_complaint"])

            symptoms = state["medical_entities"].get("symptoms", [])
            if isinstance(symptoms, list):
                query_parts.extend(symptoms[:3])

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

    async def extract_medical_entities_internal(self, text: str) -> Dict:
        """
        Uses LLM to extract structured medical entities from clinical text.
        Cleans markdown JSON safely.
        """

        prompt = prompts.ENTITY_EXTRACTION_PROMPT.format(text=text)

        response = await self.llm.ainvoke(prompt)

        raw = response.content.strip()

        # 🔥 FIX: CLEAN ```json ``` BLOCKS
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            entities = json.loads(raw)
        except Exception:
            entities = {
                "chief_complaint": "not specified",
                "symptoms": [],
                "pain_assessment": {},
            }

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
            
            # Search through loaded guidelines
            for guideline in self.medical_guidelines:
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
                risk_factors["red_flags"] = min(len(red_flags) * 2, 10)
            
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

    # ---------------------------
    # SINGLE ENTRY POINT (LOCKED)
    # ---------------------------

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
            "messages": []
        }

        final_state = await self.workflow.ainvoke(initial_state)
        return final_state

