# Stage 1: In-Memory RAG

`POST /api/stage-1/chat` · `backend/app/stages/stage_1_in_memory/router.py`

Same as Stage 0, but now we hand the LLM our actual shipping policy before it answers.

```
Question -> system prompt + full policy + messages -> gpt-4o-mini -> answer from our policy
```

## What we did

--> Read the policy file on every request
   -> `docs/sample_data/shipping_policy.txt` is read from disk each time someone asks a question.

--> Put the whole policy inside the system prompt
   -> "Answer STRICTLY from this policy."
   -> "If it's not in the policy, say: I do not have this information in the official shipping policy."
   -> The policy sits inside `<policy_document>` tags, so the LLM knows where it starts and ends.

--> Combined the system prompt + the user's messages
   -> Same as Stage 0.

--> Called the LLM
   -> Model: `gpt-4o-mini`
   -> Temperature: `0.0`, so the same question always gets the same answer.

--> Sent back the answer + token counts + the policy we used (`retrieved_context`)
   -> The frontend shows it under "Retrieved context", so you can see exactly what the LLM was given.

## Key points

-> **It works now:** COD fee → "INR 50" (Stage 0 guessed ₹40). International shipping → "I do not have this information." No guessing.

-> **Why temperature 0.0?** These are policy facts. We want the same answer every time, not creative ones.

-> **"RAG" here is the simplest kind:** no searching, we just send the whole document every time.

-> **The cost:** every question now uses ~600 tokens instead of ~30, because the whole policy goes along each time. Fine for 1 page. A 50-page policy would be slow, expensive, and may not even fit. Stage 2 fixes this by sending only the relevant parts.

-> **Policy changes:** we read the file on every request, so edits show up right away. No restart needed.

-> **Bug we hit:** the file path went up one folder too few, so the policy was never found. The code quietly used "No shipping policy document found." as the policy, and every answer became "I do not have this information." Fixed with `parents[4]`.
