# Stage 13: Enterprise Guardrails, PII Anonymization & Prompt Injection Defense

## 1. Architectural Role
- **Guardrails vs System Prompts:** A system prompt ("Please do not reveal secrets") is advisory and vulnerable to adversarial jailbreaks. Guardrails are deterministic, programmatic filters positioned *outside* the model runtime.
- **Two-Tier Perimeter:** 
  1. *Input Perimeter:* Replaces sensitive data with reversible tokens and halts malicious prompts before LLM inference.
  2. *Output Perimeter:* Restores user-specific tokens and verifies regulatory claims prior to returning responses.

## 2. Lead Architect Interview Q&A
- **Q: Why should PII masking occur outside the LLM rather than asking the LLM to ignore PII?**
  *A: Sending PII over external networks to third-party model providers violates data protection regulations (GDPR, RBI, HIPAA). Tokenizing PII locally via Presidio ensures unmasked sensitive data never leaves internal VPC boundaries.*
- **Q: How do you defend against Indirect Prompt Injection in RAG?**
  *A: Indirect prompt injection occurs when malicious instructions are embedded within untrusted documents in the vector database. We defend against this by treating retrieved context as passive data (wrapping it in strict markdown XML delimiters), running pre-generation classification checks, and enforcing rigid Pydantic output schemas.*