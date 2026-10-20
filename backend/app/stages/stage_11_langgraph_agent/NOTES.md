# Stage 11: LangGraph State Machine Architecture

## 1. Core Architecture
- **StateGraph:** Represents the entire system as a Directed Cyclic Graph. Unlike LCEL chains which are strictly acyclic, LangGraph allows loops, retries, and multi-turn reasoning cycles.
- **AgentState:** A TypedDict using the `add_messages` reducer to append incoming messages to history without overwriting.
- **ToolNode:** Executes requested tool calls dynamically in a dedicated execution step.
- **Loop Guards:** Explicitly capped at `loop_count >= 5` to prevent non-deterministic infinite loops and API token exhaustion.

## 2. Interview Q&A (Lead AI Architect)
- **Q: Why use LangGraph instead of writing a standard Python while-loop for an agent?**
  *A: A while-loop quickly degrades into unmaintainable spaghetti when handling multiple tools, error states, and rollbacks. LangGraph formalizes execution into an explicit State Machine with typed nodes and conditional edges. It also enables enterprise features like checkpointing (saving state to PostgreSQL), time-travel debugging, and Human-in-the-Loop approval workflows.*
- **Q: What is a Reducer in LangGraph state?**
  *A: By default, returning a key in a node's dictionary overwrites that state variable. A reducer function (like `add_messages`) defines how new node updates merge into existing state—appending new messages to the sequence instead of wiping previous conversation history.*