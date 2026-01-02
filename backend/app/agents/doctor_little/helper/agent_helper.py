


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
        """Fallback entity extraction using simple pattern matching"""
        entities = {
            "chief_complaint": "not specified",
            "symptoms": [],
            "medications": [],
            "allergies": [],
            "medical_history": [],
            "pain_assessment": {},
            "extraction_confidence": 0.7,
            "processing_time": datetime.now().timestamp(),
            "text_length": len(text),
            "entities_found": 0
        }
        
        text_lower = text.lower()
        
        # Simple symptom detection
        symptoms = ["chest pain", "shortness of breath", "headache", "nausea", "fever"]
        entities["symptoms"] = [s for s in symptoms if s in text_lower]
        
        # Simple pain scale detection
        import re
        pain_match = re.search(r'(\d+)\s*(?:out of|/)\s*10', text_lower)
        if pain_match:
            entities["pain_assessment"]["severity"] = int(pain_match.group(1))
        
        # Simple chief complaint detection
        if "chest pain" in text_lower:
            entities["chief_complaint"] = "chest pain"
        elif "headache" in text_lower:
            entities["chief_complaint"] = "headache"
        elif entities["symptoms"]:
            entities["chief_complaint"] = entities["symptoms"][0]
        
        entities["entities_found"] = len([k for k, v in entities.items() if v and v != "not specified"])
        
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
        if pain.get("severity"):
            parts.append(f"Pain severity: {pain['severity']}/10")
        
        return ". ".join(parts) + "." if parts else "Patient history to be obtained."

    def _generate_objective_section(self, entities: Dict) -> str:
        """Generate SOAP Objective section"""
        parts = []
        
        vitals = entities.get("vital_signs", {})
        if vitals:
            vital_strings = [f"{k}: {v}" for k, v in vitals.items()]
            parts.append(f"Vital signs: {', '.join(vital_strings)}")
        
        physical = entities.get("physical_findings", [])
        if physical:
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
        
        for code_info in self.icd10_codes:
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