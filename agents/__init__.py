"""
Agents package for SHIELD PHARMA-HYBRID system
Multi-agent medical prescription analysis system using Anthropic Managed Agents
"""

from .agent_ocr_vision import AgentOCRVision
from .agent_rag_drug import AgentRAGDrug
from .agent_google_pharmacy import AgentGooglePharmacy
from .agent_orchestrator import AgentOrchestrator

__all__ = [
    "AgentOCRVision",
    "AgentRAGDrug",
    "AgentGooglePharmacy",
    "AgentOrchestrator"
]

__version__ = "21.0"
