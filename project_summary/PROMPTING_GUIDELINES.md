# Prompting & AI Development Guidelines

This document provides practical prompting templates, design rules, and operational guidance for working with LLMs in this project.

## Purpose
- Make prompts reliable, repeatable, and auditable.
- Reduce hallucinations and ensure safety/privacy.
- Standardize prompt format for summarization, retrieval, QA, and agent orchestration.

## Core Principles
- Be explicit: describe role, goal, input format, and output constraints.
- Keep context minimal and relevant: prefer concise context windows.
- Use structured outputs: JSON or clearly delimited blocks for parsable answers.
- Fail safe: include instructions for "I don't know" when model is uncertain.
- Version and test prompts: store canonical prompts and test cases.

## Prompt Structure (recommended)
1. System instruction (role & global rules)
2. Few-shot examples (if needed)
3. Task description & constraints
4. Context (document text or retrieved passages)
5. Output schema (exact format: JSON keys, length limits)

## Templates
- Summarization (short):

System: You are a concise summarizer. Only use the text provided.

User: Summarize the text below in 3–5 bullet points, each <= 30 words.

Context:
```
{document_text}
```

Output format: JSON {"summary_bullets": ["...","..."]}

- Q&A w/ retrieval:

System: You are an expert assistant. Answer only using the provided context. If the answer isn't in context, reply "NOT_IN_CONTEXT".

User: Answer the question based on context.

Context:
```
{retrieved_passages}
```

Question: {question}

Output format: JSON {"answer": "...", "sources": ["doc1:page#"]}

- Clarification prompt (when input ambiguous):

System: If the user's request lacks critical info, ask at most one clarifying question.

User: {user_input}

Output: Ask a single clarifying question or proceed.

## Agent / Tooling Guidelines
- Keep tool contracts strict: define inputs, outputs, and error codes for every tool.
- Prefer short-lived contexts for tools to avoid state explosion.
- Log tool calls and model responses for auditing.
- Validate model outputs with deterministic checks (regex, schema validation) before executing.

## Parameters & Settings (recommendations)
- Temperature: 0.0–0.3 for factual summarization; 0.7+ for creative explorations.
- Max tokens: set conservative limits and truncate context when necessary.
- Retries: implement deterministic retry/backoff and compare outputs for stability.

## Safety, Privacy & PII
- Never include PII in prompts sent to third-party LLMs unless encrypted and approved.
- Strip/extract redaction rules for sensitive documents before sending context.
- Record minimal context in logs; never log raw PII.

## Testing & Evaluation
- Create unit tests using canned prompts and expected outputs.
- Maintain a prompt-regression suite to detect quality regressions.
- Use human review samples regularly to track precision/recall and hallucination rates.

## Prompt Versioning & Change Control
- Store canonical prompts in repository with semantic versioning (e.g., summarizer-v1.2).
- Place tests near prompts and require passing tests for prompt changes.

## Do's and Don'ts (short)
- Do: Use explicit output schemas, test prompts, and guardrails.
- Don't: Rely on unconstrained free-text replies for downstream automation.
- Do: Validate outputs before acting (e.g., DB insert, file write).
- Don't: Send full raw repositories or sensitive certificates in prompts.

## Example Prompts
- Summarize PDF: (see Summarization template above)
- Regenerate summary only if `regenerate` flag is true; otherwise return cached.

## Logging & Observability
- Log prompt id, prompt version, truncated context hash, model name, and response checksum.
- Track response latency, token usage, and error rates for cost monitoring.

## Deployment Tips
- Use a small, deterministic prompt for production-critical workflows.
- Canary updates to prompt changes and monitor regression metrics.
- Keep a manual kill-switch to route traffic away from new prompts.

---
If you'd like, I can also: export these to CSV/Google Sheets format, add suggested short answers for interview questions, or create a sample prompt-regression test harness.