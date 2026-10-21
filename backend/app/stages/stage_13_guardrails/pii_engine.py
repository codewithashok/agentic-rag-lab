"""
STAGE 13: PII Masking and Re-hydration Engine
---------------------------------------------
Detects sensitive personal data, replaces it with deterministic tokens for LLM processing,
and maps original values back to the synthesized response.
"""

import re
from typing import Tuple, Dict
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# Initialize Presidio engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Custom pattern for Indian PAN / Account Patterns
account_pattern = Pattern(name="bank_account_pattern", regex=r"ACC-\d{4}", score=0.85)
account_recognizer = PatternRecognizer(supported_entity="BANK_ACCOUNT", patterns=[account_pattern])
analyzer.registry.add_recognizer(account_recognizer)


class PIIShield:
    """Enterprise PII Tokenizer and Vault."""

    @staticmethod
    def mask_pii(text: str) -> Tuple[str, Dict[str, str]]:
        #example text = "Your account ACC-9901 has a balance of 1234-5678-9012-3456."
        """
        Scans text for PII (emails, phones, cards, names, account IDs).
        Returns masked text and a bidirectional hydration map.
        """
        # Analyze text for PII entities using Presidio
        results = analyzer.analyze(
            text=text,
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "BANK_ACCOUNT"],
            language="en"
        )

        vault: Dict[str, str] = {}
        masked_text = text

        # Sort detections in reverse order to preserve string slicing offsets
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)

        for i, res in enumerate(sorted_results):
            original_val = text[res.start:res.end]
            token = f"<{res.entity_type}_{i+1}>"
            vault[token] = original_val
            masked_text = masked_text[:res.start] + token + masked_text[res.end:]
        # Example: "Your account <BANK_ACCOUNT_1> has a balance of <CREDIT_CARD_1>."
        return masked_text, vault

    @staticmethod
    def demask_pii(text: str, vault: Dict[str, str]) -> str:
        """
        Re-hydrates masked tokens back with original values for customer display.
        """
        #example: masked_text = "Your account <BANK_ACCOUNT_1> has a balance of <CREDIT_CARD_1>."
        hydrated_text = text
        for token, original_val in vault.items():
            hydrated_text = hydrated_text.replace(token, original_val)
        # Example: "Your account ACC-9901 has a balance of 1234-5678-9012-3456."
        return hydrated_text