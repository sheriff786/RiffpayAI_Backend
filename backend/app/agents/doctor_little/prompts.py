ENTITY_EXTRACTION_PROMPT = """
As a medical NLP specialist, extract and structure the following medical entities from this clinical text:

Clinical Text: "{text}"

Extract and return a JSON object with these categories:
1. chief_complaint
2. symptoms
3. medications
4. allergies
5. medical_history
6. vital_signs
7. physical_findings
8. pain_assessment
9. timeline
10. risk_factors
11. red_flags
12. social_history
13. family_history

Include confidence scores.
"""

IMAGE_ANALYSIS_BASE_PROMPT = """
You are a medical AI assistant specializing in image analysis.
Analyze this medical image and provide:
1. Visual Description
2. Anatomical Structures
3. Abnormal Findings
4. Clinical Significance
5. Recommendations
6. Confidence Level
"""
