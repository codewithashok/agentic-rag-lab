# Stage 7: LangChain Core Primitives & LCEL Deconstructed

## 1. Why Does LangChain Exist? What Problem Does It Solve?
Without LangChain, building LLM pipelines requires writing boilerplate code for:
- Manual string formatting and prompt interpolation.
- Provider-specific API schemas (OpenAI vs Claude vs Mistral).
- Fragile `json.loads()` parsing with manual retry loops when LLMs emit malformed JSON.
- Manual wiring of asynchronous streaming and token tracing.

## 2. Core Primitives Mastered in This Stage
1. **`ChatOpenAI`**: Provider abstraction supporting uniform `.invoke()`, `.ainvoke()`, and `.astream()`.
2. **`ChatPromptTemplate`**: Type-safe prompt construction with runtime variable binding.
3. **Structured Output (`.with_structured_output`)**: Leverages OpenAI Function / Tool Calling under the hood to guarantee that responses strictly match a Pydantic class schema.
4. **LCEL (LangChain Expression Language)**: The Unix pipe syntax (`RunnableSequence`) connecting `Prompt | LLM | Parser` into an asynchronous, observable pipeline.

## 3. Interview Cheat Sheet (Lead AI Architect)
- **Q: Why use LCEL instead of standard Python functions?**
  *A: LCEL implements the `Runnable` protocol across all components. It natively provides out-of-the-box asynchronous execution (`ainvoke`), incremental streaming (`astream`), parallel batching (`abatch`), and automatic integration with distributed tracing platforms like LangSmith without rewriting code.*
- **Q: How does LangChain guarantee valid JSON from LLMs?**
  *A: It binds a Pydantic schema to the model using OpenAI/Anthropic native function-calling interfaces (Tools API) or JSON Schema mode, rather than just asking for JSON in a raw text prompt.*