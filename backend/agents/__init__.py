"""
Agent implementations live in this package now (v0.5).
Legacy `backend/agents.py` is a thin shim that re-exports the same surface.
"""
from .persona_narrator import wrap_with_persona, PersonaContext
from .question_generator import generate_question

__all__ = ["wrap_with_persona", "PersonaContext", "generate_question"]
