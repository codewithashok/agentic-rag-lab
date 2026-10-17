# Stage 0: Baseline (No RAG)

`POST /api/stage-0/chat` · `backend/app/stages/stage_0_baseline/router.py`

Here we're just asking the LLM directly. No company data. This is our "before" picture.

```
Question -> system prompt + messages -> gpt-4o-mini -> answer
```

## What we did

--> Created a route `/chat`
   -> Mounted under `/api`, so the full URL is `/api/stage-0/chat`.

--> Created a system prompt
   -> Before the actual question, we tell the LLM who it is: "You're a customer support assistant for an Indian e-commerce platform."
   -> Just the role. No facts about our policy.

--> Combined the system prompt + the user's messages
   -> System prompt goes first, then the chat.

--> Called the LLM
   -> Model: `gpt-4o-mini`
   -> Messages: the combined list
   -> Temperature: `0.2`. If we skip it, OpenAI uses `1.0`.

--> Sent back the answer + token counts
   -> Tokens are what OpenAI bills us for, so we track them from day one.

## Key points

-> **Why gpt-4o-mini?** Cheap and fast. We test a lot, and this stage doesn't need a smart model.

-> **Why temperature 0.2?** Lower means the same question gets the same answer. Higher gets more creative. For support we want consistent answers.

-> **Chat history:** the backend doesn't remember anything. The frontend sends the whole chat every time, so the LLM still sees earlier messages. Downside: tokens grow with every message.

-> **The problem:** the LLM doesn't know our policy, so it guesses. We asked for the COD fee and it said "₹40". The real fee is ₹50. Stage 1 fixes this.
