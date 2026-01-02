# app/mcp/server.py

from mcp.server.fastmcp import FastMCP
from app.agents.doctor_little.agent import DoctorLittleAgent
from app.mcp.tools import register_doctor_little_tools

# Create MCP server
mcp = FastMCP(
    name="doctor-little-mcp",
    description="Doctor Little MCP Server – Medical AI Agent"
)

# Initialize agent
agent = DoctorLittleAgent()

# Register tools
register_doctor_little_tools(mcp, agent)

def main():
    # Start MCP server (stdio mode)
    mcp.run()

if __name__ == "__main__":
    main()

# app/mcp/server.py

from mcp.server.fastapi import MCPFastAPI
from app.agents.doctor_little.agent import DoctorLittleAgent

# Create MCP server
app = MCPFastAPI(
    title="Doctor Little MCP Server",
    description="Medical reasoning tools via MCP",
    version="0.1.0",
)

# Initialize agent
doctor_agent = DoctorLittleAgent()

# ----------------------------
# Register tools
# ----------------------------

@app.tool()
async def extract_medical_entities(text: str):
    """
    Extract structured medical entities from clinical text
    """
    return await doctor_agent.extract_medical_entities_internal(text)


@app.tool()
async def assess_clinical_risk(entities: dict):
    """
    Assess clinical risk based on extracted entities
    """
    return await doctor_agent.assess_clinical_risk_internal(
        entities,
        evidence={"results": []},
    )


@app.tool()
async def generate_clinical_documentation(
    entities: dict,
    risk_assessment: dict,
    template_type: str = "SOAP",
):
    """
    Generate structured clinical documentation
    """
    return await doctor_agent.generate_clinical_documentation_internal(
        entities,
        risk_assessment,
        template_type,
    )

