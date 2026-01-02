# app/mcp/tools.py

from mcp.server.fastmcp import FastMCP
from typing import Dict


def register_doctor_little_tools(mcp: FastMCP, agent):
    """
    Register DoctorLittle tools with MCP server
    """

    @mcp.tool()
    async def extract_medical_entities(text: str) -> Dict:
        """
        Extract structured medical entities from clinical text.
        """
        return await agent.extract_medical_entities_internal(text)

    @mcp.tool()
    async def search_clinical_evidence(query: str, max_results: int = 5) -> Dict:
        """
        Search clinical guidelines and evidence.
        """
        return await agent.search_clinical_evidence_internal(query, max_results)

    @mcp.tool()
    async def assess_clinical_risk(entities: Dict, evidence: Dict) -> Dict:
        """
        Assess patient clinical risk.
        """
        return await agent.assess_clinical_risk_internal(entities, evidence)

    @mcp.tool()
    async def generate_clinical_documentation(
        entities: Dict,
        risk_assessment: Dict,
        template_type: str = "SOAP"
    ) -> Dict:
        """
        Generate structured clinical documentation.
        """
        return await agent.generate_clinical_documentation_internal(
            entities, risk_assessment, template_type
        )
