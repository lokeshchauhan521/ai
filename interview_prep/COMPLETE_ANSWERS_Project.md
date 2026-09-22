
This document provides detailed, comprehensive answers to all 34 interview questions and deep-dives into prompting strategies with real code examples.

---

# PART 1: INTERVIEW QUESTION ANSWERS (1-34)

## A. MANAGER / PRODUCT-LEVEL QUESTIONS

### Q1: What problem does this service solve and who are the primary users?

**Answer:**
- **Problem Solved**: Enterprises struggle with information extraction from unstructured PDF documents. Manual reading is time-consuming; existing tools lack domain context and personalization for complex documents.
- **Core Value Proposition**: Automated, intelligent PDF summarization + context-aware Q&A using AI, enabling users to quickly extract insights without reading entire documents.
- **Primary Users**:
  1. **Business Analysts**: Extract market research, competitor analysis from PDFs
  2. **Legal Teams**: Summarize contracts, regulatory documents, case files
  3. **Product Teams**: Analyze customer feedback, technical specs from documents
  4. **Knowledge Workers**: Quick document understanding in healthcare, financial docs, etc.
- **Key Differentiator**: Real-time, interactive chat over documents with caching/performance optimization makes it faster and cheaper than competitors.

---

### Q2: What are the main success metrics you would track for this project?

**Answer:**
- **User Adoption**: DAU (Daily Active Users), session frequency, retention rate (30/60/90-day)
- **Engagement**: Avg queries per session, time spent in chat, document upload frequency
- **Performance**:
  - Summary generation time (target: <10s for typical PDF)
  - Q&A response latency (target: <2s for cached, <5s for retrieval)
  - API uptime (target: 99.9%)
- **Quality Metrics**:
  - LLM response accuracy (A/B testing, user feedback thumbs up/down)
  - Hallucination rate (manual review of 5% sample)
  - Summary informativeness (ROUGE score vs human-written summaries)
- **Cost Metrics**:
  - Cost per document processed
  - LLM API spend, infrastructure cost per user
  - Cost per query
- **Business**:
  - Revenue per user (if SaaS)
  - Churn rate
  - NPS (Net Promoter Score) from user surveys

---

### Q3: How would you prioritize features (summarization, retrieval, multi-user chat, analytics)?

**Answer:**
**Phase 1 (MVP - Weeks 1-4)**:
- ✅ Single PDF summarization (core value)
- ✅ Basic Q&A over one document
- ✅ WebSocket real-time responses
- ❌ Multi-user, analytics

**Phase 2 (Weeks 5-8)**:
- ✅ Multi-user chat + message history
- ✅ Caching (Redis) for performance
- ✅ Basic analytics (usage dashboard)
- ✅ Bulk document upload

**Phase 3 (Weeks 9-12)**:
- ✅ Advanced retrieval (multi-document Q&A)
- ✅ Permission/access control per document
- ✅ Granular audit logs
- ✅ Custom LLM model selection

**Rationale**:
- Summarization + Q&A solve the core problem
- Multi-user enables business relevance
- Analytics validates product-market fit before heavy engineering

---

### Q4: What are the main risks (technical, data, privacy) and how would you mitigate them?

**Answer:**

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **LLM Hallucinations** | Incorrect info given to users | Source-grounded retrieval only; prompt constraints; human review of top 5% |
| **PII Exposure** | Legal/compliance liability | Redaction rules for PII patterns (SSN, email); encrypt at rest; audit logs |
| **API Rate Limits** | Service downtime/cost overruns | Queue requests; implement caching; fallback to cached summaries; budget alerts |
| **Data Loss** | PDFs/summaries lost | S3 + DB redundancy; regular backups; immutable logs |
| **Concurrent Connection Spike** | WebSocket crash | Load testing; auto-scaling; circuit breaker pattern; graceful degradation |
| **Kafka Msg Loss** | Chat history missing | At-least-once delivery; consumer offset management; dead-letter queue |
| **S3 Outage** | Embeddings unavailable | Local Chroma fallback; regional redundancy; quick recreate from source |

---

### Q5: How do you plan capacity and scaling for spikes in concurrent WebSocket connections?

**Answer:**
- **Load Testing**: Simulate 1K, 10K, 100K concurrent connections; measure latency, memory, CPU.
- **Horizontal Scaling**:
  - Multiple FastAPI instances behind load balancer (NginX/AWS ALB)
  - Sticky sessions for stateful WebSocket connections
  - Kafka for decoupling consumers from producers
- **Vertical Scaling** (short-term):
  - Increase CPU/RAM per instance
  - Database connection pooling
- **Caching Layer**:
  - Redis for summary cache (avoid re-computing)
  - Chroma embeddings cached locally (avoid S3 downloads on every query)
- **Auto-scaling Policy**:
  - Trigger: When avg response latency > 3s or CPU > 70%
  - Scale up/down with 30-second cooldown
  - Min replicas: 2, Max: 20 (example)
- **Monitoring**:
  - CloudWatch/Prometheus for CPU, memory, response time, error rate
  - Alert on latency p99 > 5s

---

### Q6: If you had to cut scope for an MVP, what would you remove and why?

**Answer:**
**Keep**:
- PDF upload & summarization (core value)
- Single-user Q&A (demo-able)
- WebSocket endpoint (real-time UX)

**Remove**:
- Multi-user chat (can bolt on later; MVP = single user per session)
- Analytics dashboard (not user-facing; don't need it to prove value)
- Multi-region deployment (nice-to-have; start in one region)
- Fine-tuned LLM model (stock OpenAI sufficient)
- Advanced access controls (assume trust for beta users)

**Result**: 50% less code, 2-week faster launch, validates core hypothesis (users want AI doc summarization) before investing in collaboration features.

---

## B. ARCHITECTURE & DESIGN QUESTIONS

### Q7: Explain the end-to-end flow from client to summary generation.

**Answer:**
```
1. Client (browser/app)
   ↓
2. Opens WebSocket: POST /summarize/{product_id}
   ↓
3. Server receives request → check DB cache
   ├─ If cached & fresh: send cached summary to client → DONE
   └─ If missing/stale → continue
   ↓
4. Fetch PDF from local storage (or S3 if on another server)
   ↓
5. Load PDF via PyPDFLoader (LangChain)
   ├─ Extract text
   ├─ Split into chunks (2000 chars, 500 overlap)
   ↓
6. Async Summarization Chain:
   - Map: Summarize each chunk via LLM (temperature=0.3)
   - Reduce: Combine summaries into sub-summaries
   - Final: Generate concise final summary
   ↓
7. Store summary in DB & Redis (cache)
   ↓
8. Send summary via WebSocket to client
   ↓
9. Client receives summary over WebSocket
```

**Why WebSocket**: Streaming response allows client to show "generating..." then update with result. HTTP would require full wait.

---

### Q8: Why use WebSockets for this app instead of HTTP REST only?

**Answer:**

| Feature | WebSocket | HTTP REST |
|---------|-----------|-----------|
| **Connection** | Persistent bidirectional | Request-response only |
| **Latency** | Low (one TCP connection) | Higher (new connection per request) |
| **Message Queue** | Server can push to client | Client must poll (inefficient) |
| **Real-time Chat** | Native; easy to add | Polling needed; poor UX |
| **Scaling** | Fewer connections per resource | Many connections; harder to scale |
| **Overhead** | Lower per-message | Protocol overhead per request |

**Example**:
- **WebSocket**: Server sends "Summarizing..." → waits → sends summary (smooth UX)
- **HTTP**: Client polls /status every 500ms (wasteful, laggy)

**Decision**: WebSocket for real-time summary streaming + chat; REST for login/static config.

---

### Q9: How are embeddings created, persisted and re-used in this system?

**Answer:**
```
1. PDF Uploaded for Product X
   ↓
2. First Time: Generate Embeddings
   - Load PDF
   - Split into chunks (2000 chars)
   - Call OpenAI Embeddings API (text-embedding-3-small)
   - Each chunk → 1536-dim vector
   ↓
3. Persist Embeddings Locally
   - Chroma vector DB stores vectors + metadata locally
   - Location: /chroma_files/{product_id}/
   - Also save full embedding dir to S3 for backup
   ↓
4. Re-use on Subsequent Queries
   - User asks Q&A for Product X
   - System checks: Does local Chroma DB exist? → YES
   - Load pre-computed vectors from /chroma_files/{product_id}/
   - No need to re-embed! (saves $$$)
   ↓
5. If Chroma Missing
   - Check S3 backup → download
   - Or re-generate from PDF (fallback)
```

**Cost Saving**:
- Embedding 1000-page PDF: $0.50 (one-time)
- Querying 100 times: $0 (reuse local vectors)
- Without caching: $0.50 × 100 = $50

---

### Q10: Describe how Kafka is used in the chat flow and why a message broker was chosen.

**Answer:**
```
Chat Flow with Kafka:

User A sends Q → FastAPI endpoint
    ↓
produce_message(topic="chat_qa", key="user_123:product_456", message={question, answer})
    ↓
Kafka Topic (partitioned by topic_key)
    ↓
Consumer (WebSocket endpoint for User A)
    ↓
consume_message() filters by topic_key
    ↓
Sends JSON to User A's WebSocket
```

**Why Kafka (vs direct socket emit)**:
- **Decoupling**: Producers don't wait for consumers (asynchronous)
- **Durability**: Messages persist if consumer temporarily offline
- **Scale**: Handle thousands of concurrent producers/consumers
- **Replay**: Consumer can rewind to re-read message history
- **Reliability**: At-least-once delivery guarantee

**Alternative (Direct WebSocket Emit)**:
- If producer crashes before sending, message lost forever
- Harder to scale (need in-memory queue per instance)
- No replay capability

---

### Q11: How would you design the system to support multi-region deployment and low latency?

**Answer:**
```
Regional Setup:
┌─────────────────────────────────────┐
│  CloudFront CDN (global)            │
│  (routes requests to nearest region)│
└──────┬──────────────────────┬───────┘
       │                      │
   US-East               Asia-Southeast
   ┌─────────────────┐  ┌─────────────────┐
   │ FastAPI Servers │  │ FastAPI Servers │
   │ Chroma Local    │  │ Chroma Local    │
   │ Redis Cache     │  │ Redis Cache     │
   │ PostgreSQL DB   │  │ PostgreSQL DB   │
   └──────┬──────────┘  └────────┬────────┘
          │                      │
         S3 (global, replicated) - All PDFs stored globally
         
         Kafka Clusters (per region, cross-replicated for messages)
```

**Latency Reduction**:
- Local Chroma per region (no cross-region embedding queries)
- Regional Redis cache (fast summary lookup)
- S3 regional endpoints (multipart download)
- CloudFront caches responses (CDN)

**Consistency**:
- Kafka replication factor = 2 (data survives one node failure)
- DB read replicas for read scaling
- Eventual consistency acceptable for summaries (users tolerate brief stale data)

---

### Q12: What are the critical single points of failure and how to make them resilient?

**Answer:**

| SPOF | Mitigation |
|------|-----------|
| **LLM API Outage** | Fallback to cached summary; queue requests; notify user "Try later" |
| **S3 Outage** | Recreate embeddings on-the-fly (slower); local backup (NAS); use regional replicas |
| **Database Outage** | Read replicas; failover to standby instance; async writes to queue |
| **Kafka Cluster Down** | Consumer buffers messages locally; producer retries w/ backoff |
| **Redis Cache Down** | Fall through to DB (slower); no user-facing impact |
| **Single FastAPI Instance** | Run ≥2 instances behind load balancer; health checks |
| **Network Partition** | Sticky sessions (if A goes down, session lost); client reconnects to B |

**High Availability Setup**:
```
Load Balancer (AWS ELB)
    ├─ FastAPI Instance 1 (health check every 10s)
    ├─ FastAPI Instance 2
    └─ FastAPI Instance 3

DB: Primary + 2 read replicas
Redis: sentinel mode (3 nodes, auto-failover)
Kafka: 3 broker cluster, replication factor 2
```

---

## C. DATA, STORAGE & INTEGRATIONS

### Q13: Where and how do we store generated summaries, and how is cache invalidation handled?

**Answer:**
```
Storage Hierarchy:

Redis Cache (L1) - in-memory, fast, volatile
    ├─ Key: f"summary:{product_id}"
    ├─ TTL: 1 hour (auto-expire)
    ├─ Lookup time: <1ms
    └─ Used for: Serving repeated queries

PostgreSQL DB (L2) - persistent, durable
    ├─ Table: summaries
    ├─ Columns: product_id, summary_text, created_at, regenerate (boolean)
    ├─ Lookup time: ~10ms
    └─ Used for: Primary storage, user audit trail

S3 Backup (L3) - archive, not queried frequently
    ├─ Path: s3://summaries-backup/{product_id}/summary.txt
    ├─ Used for: Disaster recovery, compliance
    └─ Lookup time: seconds (rarely used)
```

**Cache Invalidation**:
```python
# When summary needs refresh (e.g., PDF updated):
1. User clicks "Regenerate Summary"
2. Set DB: regenerate = True for product_id
3. Delete Redis: DEL f"summary:{product_id}"
4. Trigger regeneration workflow
5. Store new summary in DB & Redis
6. Mark regenerate = False

# Automatic invalidation:
- Redis TTL (1 hour) expires → looks up DB
- DB summary marked stale → re-generate on next query
```

---

### Q14: What are the trade-offs between storing embeddings in S3 vs a managed vector DB?

**Answer:**

| Aspect | S3 + Local Chroma | Managed Vector DB (Pinecone/Weaviate) |
|--------|------------------|---------------------------------------|
| **Cost** | S3 storage (~$0.02/GB/mo) + compute | $0.25-1K/mo (subscription) |
| **Latency** | ~500ms (download from S3) | <10ms (network call) |
| **Setup** | Self-manage Chroma, S3 syncing | Plug-and-play, no ops |
| **Scalability** | Limited by disk size per instance | Scales to billions of vectors |
| **Search Speed** | Local search (fast once downloaded) | Cloud search (always network-bound) |
| **Control** | Full control; can audit | Vendor lock-in |
| **Data Privacy** | Keep data in your infra | Data sent to third party |

**Recommendation for This Project**:
- **Phase 1**: S3 + Chroma (cheaper, private, good for <100K PDFs)
- **Phase 2**: If >100K PDFs or need sub-second search → Pinecone

**Hybrid Approach**:
```python
# Best of both worlds:
1. Query managed vector DB (Pinecone) for candidates
2. Re-rank locally in Chroma for privacy
3. Reduces costs; improves latency & control
```

---

### Q15: How would you secure the PDF storage, S3 transfers, and Kafka topics?

**Answer:**
```
PDF Storage Security:
├─ S3 Bucket: Block all public access (ACL private)
├─ Encryption: AES-256 at rest; TLS 1.2+ in transit
├─ IAM Policy: Only FastAPI role can read
└─ Expiry: Auto-delete PDFs after 90 days

S3 Transfer Security:
├─ Use presigned URLs (expire after 1 hour)
├─ IP whitelisting (only from FastAPI servers)
├─ VPC endpoint (no internet routing)
└─ MFA delete (prevent accidental removal)

Kafka Security:
├─ Authentication: SASL/SCRAM (username/password)
├─ Encryption: TLS for all connections
├─ Authorization: ACLs per topic (only allowed users/roles)
├─ Audit: Log all produce/consume events
└─ Network: Kafka in private subnet, not exposed to internet

Application Level:
├─ Rotate credentials monthly
├─ Never log PII or full PDF content
├─ Use secrets manager (AWS Secrets Manager) for keys
└─ Implement rate limiting per user (prevent abuse)
```

---

### Q16: How do you handle large PDFs and memory/CPU constraints during processing?

**Answer:**
```python
# Challenge: 500MB PDF → OutOfMemory

# Solution 1: Streaming chunked processing
def stream_process_pdf(pdf_path, chunk_size_mb=10):
    """Process PDF in 10MB chunks; don't load entire file."""
    with open(pdf_path, 'rb') as f:
        while chunk := f.read(chunk_size_mb * 1024 * 1024):
            yield process_chunk(chunk)  # Async process

# Solution 2: Lazy loading with generators
def split_pages_lazily(pdf_path):
    """Load one page at a time; don't materialize all."""
    loader = PyPDFLoader(pdf_path)
    for page in loader.load():
        yield page  # Don't load next page until requested

# Solution 3: Resource limits & timeouts
@timeout(seconds=300)  # Abort if takes >5 min
def summarize_with_limit(pdf_path):
    # Use psutil to set memory limit
    set_memory_limit(1024)  # 1GB max
    # If exceeds, raise MemoryError → graceful failure

# Solution 4: Queue overflow (if spike in requests)
# Instead of processing immediately:
if queue_size > 100:
    return {"status": "queued", "position": 50, "wait_time": "~5 min"}
# Process async; notify user when done
```

---

## D. LLMs, RETRIEVAL & PROMPTING

### Q17: How does the system decide between using a document summary versus retrieval?

**Answer:**
```python
async def get_answer(query, product_id):
    """Decide: use summary or retrieval-based answer."""
    
    # Step 1: Classify query type
    needs_summary = summary_query(query)
    # Prompt: "Is this query about the entire document 
    #         or specific details?" → True/False
    
    if needs_summary:
        # Query like: "Summarize this", "What's main idea?"
        # → Use cached summary (fast)
        summary = get_db_summary(product_id)
        answer = llm.invoke({
            "context": summary,
            "question": query
        })
    else:
        # Query like: "Find page with pricing info"
        # → Use retrieval (specific facts)
        retriever = chroma_db.as_retriever()
        docs = retriever.get_relevant_documents(query)
        answer = llm.invoke({
            "context": docs,
            "question": query
        })
    
    return answer
```

**Decision Logic**:
- **Use Summary** if: "Overview", "Main points", "What is...", "Summarize"
- **Use Retrieval** if: "Find", "Where", "How much", "Specific fact"

**Benefits**:
- Summary: Fast (1 cached lookup); good for big picture
- Retrieval: Precise (specific passages); better for details

---

### Q18: What problems might arise from hallucinations and how would you reduce them?

**Answer:**
```
Problems:
- "This document says PayPal was founded in 1999" (actually 1998)
- Plausible-sounding but false information
- Legal liability if used in contracts/compliance

Mitigation Strategies:

1. Source-Grounded Retrieval (Best)
   Prompt: "Answer only using these passages:
            {retrieved_docs}
            If not in passages, say NOT_FOUND"
   → Forces model to cite sources

2. Temperature Control
   temperature = 0.1 (very deterministic)
   → Less creative, more factual

3. Few-Shot Prompting
   Example 1:
   Q: "When was X founded?"
   A: "According to the document (page 3), X was founded in 1998."
   → Shows expected output format

4. Constraint Prompting
   "Never make up dates, numbers, or names.
    If unsure, respond: 'This information is not clearly stated.'"

5. Rating System
   confidence_score = llm_extract_confidence(response)
   if confidence < 0.7:
       return {"answer": response, "confidence": "LOW", "note": "Verify manually"}

6. Fact-Checking Loop
   extracted_facts = extract_claims(response)
   for fact in facts:
       if fact not in source_documents:
           query_again_llm("Verify: {fact}")

7. Human Review (critical docs)
   For contract summaries, legal docs:
   - Always have human review before presenting
   - Flag claims with low confidence

Example Code:
```python
def answer_with_hallucination_check(query, product_id):
    docs = retrieve_relevant_docs(query, product_id)
    
    prompt = f"""
    You are a document analyzer. Answer based ONLY on facts in these docs.
    If a fact is not explicitly stated, respond "NOT_STATED".
    
    Documents:
    {docs}
    
    Question: {query}
    
    Respond in JSON: {{"answer": "...", "confidence": "HIGH|MEDIUM|LOW", "source": "page X"}}
    """
    
    response = llm.invoke(prompt)
    
    if response['confidence'] == 'LOW':
        alert_user("This answer has low confidence; verify manually")
    
    return response
```

---

### Q19: How would you evaluate and monitor LLM quality and drift over time?

**Answer:**
```
Evaluation Framework:

1. Baseline Metrics (before launch)
   ├─ ROUGE Score (compares summary to human-written)
   │  └─ Target: ROUGE-L > 0.4
   ├─ Factual Consistency (% facts verified against source)
   │  └─ Target: > 95%
   ├─ Brevity (avg summary length in words)
   │  └─ Target: 100-150 words
   └─ User Satisfaction (thumbs up/down)
      └─ Target: > 80% positive

2. Continuous Monitoring (production)
   ├─ Monthly: Sample 100 random summaries
   │  └─ Manual review: accuracy, completeness, relevance
   ├─ Weekly: Track user engagement
   │  └─ "Thumbs down" rate (target: <5%)
   ├─ Daily: Monitor latency, error rates
   │  └─ Alert if p99 latency > 10s
   └─ Quarterly: A/B test new LLM version
       └─ Split traffic 90/10; compare metrics

3. Drift Detection
   ├─ If ROUGE score drops >10% month-over-month
   │  └─ Investigate: Did OpenAI change model? Did our data change?
   ├─ If user "thumbs down" rate > 10%
   │  └─ Alert on-call engineer
   └─ If cost per query increases >20%
       └─ Check token usage; may need prompt optimization

4. Dashboards
   ├─ Grafana dashboard: ROUGE, accuracy, cost, latency
   ├─ Looker: User satisfaction trends
   └─ Custom alerts: triggers on thresholds
```

---