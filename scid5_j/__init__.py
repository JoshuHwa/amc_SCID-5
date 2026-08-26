"""SCID-5 Module J (adjustment disorder) interview agent.

Research prototype. Not a medical device and not for clinical use.
"""

from .criteria import MODULE_J, SPECIFIERS, Criterion
from .interview import CriterionResult, InterviewResult, ModuleJInterview
from .llm import Judgement, OpenAIRater, Rater

__all__ = [
    "Criterion",
    "CriterionResult",
    "InterviewResult",
    "Judgement",
    "MODULE_J",
    "ModuleJInterview",
    "OpenAIRater",
    "Rater",
    "SPECIFIERS",
]
__version__ = "2.0.0"
