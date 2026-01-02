from dotenv import load_dotenv
import os


load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

from fastapi import FastAPI
from app.api.consult import router as consult_router

app = FastAPI(
    title="Doctor Little Backend",
    description="AI Medical Consultation Backend (LangGraph + MCP + Coral-ready)",
    version="1.0.0",
)

# Health check (IMPORTANT)
@app.get("/")
def root():
    return {"status": "Doctor Little API is running"}

# Register API routes
app.include_router(
    consult_router,
    prefix="/api",
    tags=["Consultation"]
)





