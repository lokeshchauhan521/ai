# Interview Question Sheet — AI Analysis Service

This document contains 30 suggested interview questions (manager and technical rounds) related to the project, grouped by topic. Use these to prepare answers and talking points.

## A. Manager / Product-level (6)
1. What problem does this service solve and who are the primary users? — (Product/Value)
2. What are the main success metrics you would track for this project? — (Metrics)
3. How would you prioritize features (summarization, retrieval, multi-user chat, analytics)? — (Prioritization)
4. What are the main risks (technical, data, privacy) and how would you mitigate them? — (Risks)
5. How do you plan capacity and scaling for spikes in concurrent WebSocket connections? — (Scaling)
6. If you had to cut scope for an MVP, what would you remove and why? — (MVP)

## B. Architecture & Design (6)
7. Explain the end-to-end flow from client to summary generation. — (Flow)
8. Why use WebSockets for this app instead of HTTP REST only? — (Design trade-off)
9. How are embeddings created, persisted and re-used in this system? — (Embeddings)
10. Describe how Kafka is used in the chat flow and why a message broker was chosen. — (Messaging)
11. How would you design the system to support multi-region deployment and low latency? — (Architecture)
12. What are the critical single points of failure and how to make them resilient? — (Resiliency)

## C. Data, Storage & Integrations (4)
13. Where and how do we store generated summaries, and how is cache invalidation handled? — (Data lifecycle)
14. What are the trade-offs between storing embeddings in S3 vs a managed vector DB? — (Trade-offs)
15. How would you secure the PDF storage, S3 transfers, and Kafka topics? — (Security)
16. How do you handle large PDFs and memory/CPU constraints during processing? — (Resource mgmt)

## D. LLMs, Retrieval & Prompting (6)
17. How does the system decide between using a document summary versus retrieval? — (Decision logic)
18. What problems might arise from hallucinations and how would you reduce them? — (Reliability)
19. How would you evaluate and monitor LLM quality and drift over time? — (Monitoring)
20. What prompt-engineering patterns would you use for reliable summarization? — (Prompting)
21. How would you manage rate-limits, costs and parallelism when calling the LLM? — (Cost control)
22. When would you use embeddings' similarity search vs dense retrieval models? — (Retrieval choice)

## E. Kafka, Messaging & Streaming (3)
23. How does the consumer filter messages for a particular client? — (Filtering)
24. How would you handle out-of-order or duplicate messages in the chat pipeline? — (Idempotency)
25. What delivery guarantees do you need (at-least-once, exactly-once) and why? — (Guarantees)

## F. Production, Observability & Security (3)
26. What logging, tracing and metrics would you add to troubleshoot issues in production? — (Observability)
27. What data retention and privacy controls should we implement for uploaded PDFs and generated summaries? — (Privacy)
28. How would you design testing (unit, integration, e2e) for components that call external LLMs? — (Testing)

## G. AI Coding, Tools, and Agent Comparisons (Codex vs Claude, Agents) (6)
29. If using AI coding assistants (Codex-style or Claude), what workflow steps would you follow to integrate generated code safely? — (Workflow)
30. What are the key differences between 'Codex-style' code generation and 'Claude-style' reasoning/agent approaches? — (Comparison)
31. When would you use an "extension agent" pattern vs direct LLM calls for application logic? — (Agent design)
32. How should prompts, tool-use, and state be structured when building an agent that executes steps (e.g., file ops, DB calls)? — (Agent orchestration)
33. What code review and validation steps would you enforce for AI-generated code before merging to main? — (Code safety)
34. What are the primary "do's and don'ts" when relying on AI coding tools in production? — (Best practices)


## Quick preparation tips (short answers to practice):
- Be ready to diagram the flows and justify architectural trade-offs.
- Prepare examples of how you'd test LLM outputs and improve reliability.
- Practice explaining cost-control, scaling and privacy controls clearly and succinctly.


---
Generated for the project. If you want, I can also produce suggested model answers or short bullet-point answers for each question.