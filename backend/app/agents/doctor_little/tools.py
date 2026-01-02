from langchain_core.tools import tool


class DoctorLittleTools:

    def __init__(self, agent):
        self.agent = agent

    @tool
    async def process_voice_consultation(self, audio_data: str, patient_id: str = "UNKNOWN"):
        """
        Convert patient voice audio into clinical text using speech-to-text.

        Args:
            audio_data: Base64 encoded audio
            patient_id: Unique patient identifier

        Returns:
            Transcript with confidence and metadata
        """
        return await self.agent.process_voice_consultation_internal(audio_data, patient_id)

    @tool
    async def analyze_medical_image(self, image_data: str, analysis_type: str = "general"):
        """
        Analyze a medical image (X-ray, skin image, scan) and extract findings.

        Args:
            image_data: Base64 encoded image
            analysis_type: general | radiology | dermatology

        Returns:
            Structured image analysis
        """
        return await self.agent.analyze_medical_image_internal(image_data, analysis_type)

    @tool
    async def extract_medical_entities(self, text: str):
        """
        Extract medical entities such as symptoms, chief complaint, risks.

        Args:
            text: Clinical text

        Returns:
            Structured medical entities
        """
        return await self.agent.extract_medical_entities_internal(text)

    @tool
    async def search_clinical_evidence(self, query: str, max_results: int = 5):
        """
        Search clinical guidelines and evidence based on symptoms.

        Args:
            query: Medical query
            max_results: Number of evidence items

        Returns:
            Relevant clinical evidence
        """
        return await self.agent.search_clinical_evidence_internal(query, max_results)

    @tool
    async def assess_clinical_risk(self, entities: dict, evidence: dict):
        """
        Assess patient risk level based on extracted entities and evidence.

        Args:
            entities: Medical entities
            evidence: Clinical evidence

        Returns:
            Risk score and urgency level
        """
        return await self.agent.assess_clinical_risk_internal(entities, evidence)

    @tool
    async def generate_clinical_documentation(
        self,
        entities: dict,
        risk_assessment: dict,
        template_type: str = "SOAP"
    ):
        """
        Generate structured medical documentation (SOAP, H&P, Emergency).

        Args:
            entities: Extracted medical entities
            risk_assessment: Risk analysis
            template_type: SOAP | H_AND_P | EMERGENCY

        Returns:
            Structured clinical note
        """
        return await self.agent.generate_clinical_documentation_internal(
            entities, risk_assessment, template_type
        )
