# Stage 12: Multi-Agent Collaboration & Maker-Checker Audit Loops

## 1. Architectural Distinction: Router vs Multi-Agent
- **Single Agent with Tools (Stage 11):** One LLM attempts to manage query routing, tool parameter formatting, policy research, and final drafting in a single context window. As tools scale beyond 5-10, tool hallucination and prompt interference rise sharply.
- **Multi-Agent Collaboration (Stage 12):** Decomposes operations into dedicated, narrow-scope specialists (Account Specialist, Policy Specialist) directed by a Supervisor. Employs an adversarial Maker-Checker loop to enforce compliance prior to emitting customer responses.

## 2. Lead Architect Interview Q&A
- **Q: Why implement a Maker-Checker pattern instead of asking one LLM to 'be thorough and check itself'?**
  *A: A single LLM call suffers from self-reinforcing bias: once a model hallucinates or overlooks a compliance clause during generation, asking it in the same context to verify its work frequently yields false confirmation. Separating the roles into an independent Maker and an adversarial Checker with distinct system prompts and schemas ensures true verification.*
- **Q: How does LangGraph handle loops in a multi-agent system without deadlock?**
  *A: The state machine maintains an `iteration_count` in the shared typed state. In the conditional edge exiting the Checker (`route_checker`), we evaluate both the audit verdict and the iteration limit (`iterations >= 3`). If the Maker cannot satisfy the Checker within 3 cycles, the graph breaks the loop and halts at `END` to trigger human-in-the-loop escalation.*