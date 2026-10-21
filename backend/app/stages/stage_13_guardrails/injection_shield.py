"""
STAGE 13: Prompt Injection and Jailbreak Shield
-----------------------------------------------
Evaluates prompts for prompt injection, privilege escalation,
and adversarial system instruction overrides.
"""

import re
from typing import Tuple

# Fast deterministic heuristic patterns for prompt injection
JAILBREAK_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)",
    r"bypass\s+(compliance|security|hold|verification)",
    r"system\s*:\s*override",
    r"reveal\s+(system\s+prompt|internal\s+api|api_key|secret)"
]

class InjectionShield:
    """Pre-flight adversarial classifier."""

    @staticmethod
    def inspect(prompt: str) -> Tuple[bool, str]:
        """
        Returns (is_threat, reason).
        True indicates an adversarial attack was detected.
        """
        lower_prompt = prompt.lower()

        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, lower_prompt, re.IGNORECASE):
                return True, f"Blocked: Prompt matched adversarial override pattern: '{pattern}'"

        return False, "Clean"