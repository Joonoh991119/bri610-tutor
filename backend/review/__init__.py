"""
backend.review — Multi-Lens Review loop. Load-bearing quality gate for every
user-facing artifact (questions, walkthrough steps, summaries).

Public:
    from backend.review import multi_lens_review, ReviewResult
"""
from .multi_lens import multi_lens_review, ReviewResult, Artifact

__all__ = ["multi_lens_review", "ReviewResult", "Artifact"]
