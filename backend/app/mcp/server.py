# # app/mcp/server.py

# from mcp.server.fastmcp import FastMCP
# from app.agents.doctor_little.agent import DoctorLittleAgent
# from app.mcp.tools import register_doctor_little_tools

# # Create MCP server (STDIO-based)
# mcp = FastMCP(
#     name="doctor-little-mcp"
#     # description="Doctor Little MCP Server – Medical AI Agent"
# )

# # Initialize agent
# agent = DoctorLittleAgent()

# # Register tools
# register_doctor_little_tools(mcp, agent)

# def main():
#     # This is what MCP CLI uses
#     mcp.run()

# if __name__ == "__main__":
#     main()

# app/mcp/server.py

# from mcp.server.fastmcp import FastMCP
# from agents.doctor_little.agent import DoctorLittleAgent
# from mcp.tools import register_doctor_little_tools

# # Create MCP server (STDIO-based)
# mcp = FastMCP(
#     name="doctor-little-mcp"
# )

# # Initialize agent (lazy LLM init already handled)
# agent = DoctorLittleAgent()

# # Register tools
# register_doctor_little_tools(mcp, agent)

# def main():
#     mcp.run()

# if __name__ == "__main__":
#     main()


# app/mcp/server.py

import sys
from pathlib import Path


from mcp.server.fastmcp import FastMCP

# NOW these imports WILL work
from app.agents.doctor_little.agent import DoctorLittleAgent
from app.mcp.tools import register_doctor_little_tools
from typing import Dict
mcp = FastMCP(
    name="doctor-little-mcp"
)

agent = DoctorLittleAgent()
# register_doctor_little_tools(mcp, agent)
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

def main():
    mcp.run()

if __name__ == "__main__":
    main()
