from langgraph.graph import StateGraph, START, END
from .state import MedicalConsultationState

def build_workflow(agent):
    graph = StateGraph(MedicalConsultationState)

    graph.add_node("voice_processing", agent._voice_processing_node)
    graph.add_node("image_analysis", agent._image_analysis_node)
    graph.add_node("entity_extraction", agent._entity_extraction_node)
    graph.add_node("evidence_search", agent._evidence_search_node)
    graph.add_node("risk_assessment", agent._risk_assessment_node)
    graph.add_node("documentation", agent._documentation_node)
    graph.add_node("quality_check", agent._quality_check_node)

    graph.add_edge(START, "voice_processing")
    graph.add_edge("voice_processing", "image_analysis")
    graph.add_edge("image_analysis", "entity_extraction")
    graph.add_edge("entity_extraction", "evidence_search")
    graph.add_edge("evidence_search", "risk_assessment")
    graph.add_edge("risk_assessment", "documentation")
    graph.add_edge("documentation", "quality_check")
    graph.add_edge("quality_check", END)

    return graph.compile()
