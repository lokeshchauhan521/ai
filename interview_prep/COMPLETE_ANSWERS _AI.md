### Q20: What prompt-engineering patterns would you use for reliable summarization?

**Answer:**
```python
# Pattern 1: Role-based Instruction
prompt = """
You are a professional business analyst summarizing documents.
Your goal is to extract the 3-5 most important points.
Use simple language; avoid jargon.
"""

# Pattern 2: Explicit Output Format
prompt = """
Respond in JSON with this exact structure:
{
  "summary": "2-3 sentences overview",
  "key_points": ["point1", "point2", "point3"],
  "data_points": ["number1", "number2"],
  "next_steps": "What should the reader do?"
}
"""

# Pattern 3: Few-Shot Example
prompt = """
Example:
Input: "Acme Inc. raised $10M Series A in Q3 2023 led by Sequoia..."
Output: {"summary": "Acme Inc. secured $10M Series A funding.", "key_points": ["$10M raised", "Led by Sequoia", "Q3 2023"]}

Now summarize this:
Input: {document_text}
Output:
"""

# Pattern 4: Constraint-based
prompt = """
Summarize this document following these rules:
1. Use only facts stated in the document
2. Keep summary under 150 words
3. Do NOT add opinion or external knowledge
4. Use bullet points for readability
5. If you can't find key info, say "NOT STATED"

Document:
{document_text}
"""

# Pattern 5: Temperature & Token Control
response = llm.invoke(
    prompt,
    temperature=0.2,  # Low temp → factual, consistent
    max_tokens=300,   # Prevents long-winded output
    frequency_penalty=0.5  # Reduces repetition
)

# Pattern 6: Iterative Refinement
summary_v1 = summarize(doc)
feedback = "Too long; focus on pricing and timeline"
summary_v2 = summarize(doc, feedback=feedback)
```

---

### Q21: How would you manage rate-limits, costs and parallelism when calling the LLM?

**Answer:**
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Strategy 1: Rate Limiting (token bucket)
class RateLimiter:
    def __init__(self, calls_per_minute=60):
        self.calls_per_minute = calls_per_minute
        self.semaphore = asyncio.Semaphore(calls_per_minute)
    
    async def __aenter__(self):
        await self.semaphore.acquire()
    
    async def __aexit__(self, *args):
        self.semaphore.release()
        await asyncio.sleep(60 / self.calls_per_minute)

# Strategy 2: Cost Tracking
class CostTracker:
    def __init__(self, budget_monthly=1000):
        self.budget = budget_monthly
        self.spent_today = 0
        self.spent_monthly = 0
    
    def estimate_cost(self, tokens_input, tokens_output):
        # gpt-4: $0.03 per 1K input, $0.06 per 1K output
        return (tokens_input * 0.03 + tokens_output * 0.06) / 1000
    
    async def llm_call_with_budget(self, prompt):
        estimated_cost = self.estimate_cost(len(prompt.split()), 100)
        
        if self.spent_today + estimated_cost > self.budget / 30:
            raise BudgetExceededError(f"Daily limit exceeded. Spent: ${self.spent_today}")
        
        response = await llm.ainvoke(prompt)
        actual_cost = self.estimate_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
        self.spent_daily += actual_cost
        self.spent_monthly += actual_cost
        
        return response

# Strategy 3: Batch Processing (reduce per-call overhead)
async def batch_summarize_pdfs(product_ids, batch_size=5):
    for i in range(0, len(product_ids), batch_size):
        batch = product_ids[i : i + batch_size]
        tasks = [summarize_pdf(pid) for pid in batch]
        summaries = await asyncio.gather(*tasks)  # Parallel processing
        yield summaries

# Strategy 4: Retry with Exponential Backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def llm_call_with_retry(prompt):
    try:
        return await llm.ainvoke(prompt)
    except RateLimitError:
        # If rate limited, retry with exponential backoff (2s, 4s, 8s...)
        raise

# Strategy 5: Queuing for Peak Demand
from asyncio import Queue

llm_queue = Queue(maxsize=100)

async def queue_llm_request(priority, prompt, callback):
    """Add request to queue if not at capacity."""
    if llm_queue.full():
        return {"status": "queue_full", "retry_after": 30}
    
    await llm_queue.put((priority, prompt, callback))
    return {"status": "queued", "position": llm_queue.qsize()}

async def llm_worker():
    """Consume from queue; process with rate limiting."""
    while True:
        priority, prompt, callback = await llm_queue.get()
        
        async with rate_limiter:
            response = await llm.ainvoke(prompt)
            await callback(response)
        
        llm_queue.task_done()

# Usage:
# asyncio.create_task(llm_worker())
# await queue_llm_request(priority=1, prompt="...", callback=handle_response)
```

---

### Q22: When would you use embeddings' similarity search vs dense retrieval models?

**Answer:**

| Approach | Embeddings Similarity | Dense Retrieval Models |
|----------|----------------------|----------------------|
| **Speed** | <10ms (precomputed) | 100-500ms (reranking) |
| **Accuracy** | Good for semantic match | Better for complex reasoning |
| **Example Use** | "Find docs similar to X" | "Find evidence for contract clause" |
| **Overhead** | None (vectors pre-computed) | Higher (real-time computation) |
| **Cost** | Embedding API cost (one-time) | LLM inference cost per query |

**Decision Logic**:
```python
def retrieve_docs(query, product_id, query_complexity):
    docs = []
    
    if query_complexity == "SIMPLE":
        # Just need semantically similar passages
        # Use embedding similarity + Chroma
        docs = chroma.similarity_search(query, k=5)
    
    elif query_complexity == "COMPLEX":
        # Need to reason over multiple docs
        # Use dense retrieval (e.g., ColBERT) + reranking
        candidates = chroma.similarity_search(query, k=20)
        reranked = dense_retriever.rerank(query, candidates, top_k=5)
        docs = reranked
    
    elif query_complexity == "REASONING":
        # Multi-hop reasoning needed
        # Use LLM to select docs then answer
        initial_docs = chroma.similarity_search(query, k=10)
        refined_query = llm.refine_query(query, initial_docs)
        docs = chroma.similarity_search(refined_query, k=5)
    
    return docs
```

**Examples**:
- **Embeddings**: "Find all docs about pricing" → chroma.similarity_search("pricing")
- **Dense Retrieval**: "Does this contract have a non-compete clause and what are its terms?" → ColBERT + LLM reasoning

---

## E. KAFKA, MESSAGING & STREAMING

### Q23: How does the consumer filter messages for a particular client?

**Answer:**
```python
# Kafka message structure:
# Topic: "chat_qa"
# Key: f"{user_id}:{product_id}" e.g., "user_123:product_456"
# Value: {"question": "...", "answer": "..."}

def consume_message(topic, user_id, product_id):
    """
    Consumer subscribes to topic but filters by key.
    Only receives messages for this specific user+product combo.
    """
    consumer = Consumer(bootstrap_servers=BOOTSTRAP_SERVER)
    
    # Assign specific partition (assumes partition count = 1 or manual assign)
    consumer.assign([TopicPartition(topic, 0)])
    
    # Filter: Only process messages with matching key
    expected_key = f"{user_id}:{product_id}"
    
    while True:
        msg = consumer.poll(timeout=2)
        
        if msg is None:
            continue  # No message yet
        
        if msg.error():
            break  # Error occurred
        
        # Key-based filtering
        if msg.key() and msg.key().decode('utf-8') == expected_key:
            response = msg.value().decode('utf-8')
            yield response  # Send to client only if key matches
            
# Usage (in WebSocket handler):
@app.websocket("/recieve-msg/{user_id}/{product_id}")
async def websocket_endpoint(user_id, product_id, websocket: WebSocket):
    await websocket.accept()
    
    for msg in consume_message(TOPIC_NAME, user_id, product_id):
        await websocket.send_json(eval(msg))
```

**Key Design**: Kafka key partitioning allows Kafka to route all messages for user_123:product_456 to the same partition. Our consumer then filters in-code.

**Alternative (Topic per User)**: Less efficient but simpler:
```python
# Create topic per user: "chat_qa_user_123"
# Only one consumer per user
# Pro: Natural filtering; Con: millions of topics (scaling issue)
```

---

### Q24: How would you handle out-of-order or duplicate messages in the chat pipeline?

**Answer:**
```python
# Challenge: Kafka can deliver messages out-of-order or duplicate

# Solution 1: Idempotent Consumer (track processed IDs)
class IdempotentConsumer:
    def __init__(self):
        self.processed_ids = set()  # In-memory
        self.db = PostgreSQL()  # Persistent storage
    
    async def handle_message(self, message):
        msg_id = message['id']  # Assume each message has unique ID
        
        if msg_id in self.processed_ids:
            return  # Already processed; skip
        
        # Process message (e.g., store Q&A pair)
        await self.db.insert("chat_messages", message)
        
        # Mark as processed
        self.processed_ids.add(msg_id)
        await self.db.execute("UPDATE messages_processed SET done=True WHERE id=?", msg_id)

# Solution 2: Ordered Delivery (per user)
# Kafka key = user_id → all messages for one user go to same partition
# Partition ensures order within partition
# Consumer reads sequentially → messages arrive in order

# But if consumer crashes, might re-process last message:
consumer = Consumer(auto_offset_reset='earliest')
# Options:
# - 'earliest': Re-read from start (might duplicate)
# - 'latest': Skip to end (might lose messages)
# - Committed offset: Resume from last acknowledged offset (best)

# Solution 3: Offset Commit (don't lose progress)
msg = consumer.poll()
process(msg)
consumer.commit(asynchronous=False)  # Only after processing succeeds

# Solution 4: Sequence Numbers (detect out-of-order)
messages = [
    {"seq": 1, "question": "What is X?"},
    {"seq": 3, "question": "What is Z?"},  # Out of order!
    {"seq": 2, "question": "What is Y?"}
]

def order_and_deduplicate(messages):
    seen = set()
    ordered = {}
    
    for msg in messages:
        if msg['id'] in seen:
            continue  # Duplicate
        seen.add(msg['id'])
        ordered[msg['seq']] = msg
    
    return [ordered[i] for i in sorted(ordered.keys())]

# Solution 5: Dead-Letter Queue (for unrecoverable messages)
try:
    process_message(msg)
except Exception as e:
    # Send to DLQ for manual inspection
    dlq_producer.send(topic="dlq_chat_qa", value=msg, headers=[("error", str(e))])
    logging.error(f"Sent to DLQ: {msg}")
```

**Best Practice** (Kafka + Idempotency):
- Kafka guarantees: order within partition
- Consumer should: track processed message IDs in DB
- This handles duplicates even if Kafka retransmits

---

### Q25: What delivery guarantees do you need (at-least-once, exactly-once) and why?

**Answer:**

| Guarantee | Meaning | Use Case | Tradeoff |
|-----------|---------|----------|----------|
| **At-most-once** | Message delivered 0-1x; might lose | Real-time analytics draft | Fast; unsafe |
| **At-least-once** | Message delivered ≥1x; might duplicate | Chat Q&A history | Common; needs dedup |
| **Exactly-once** | Message delivered exactly 1x | Financial txns, contract execution | Slow; safest |

**For This Project**:
```
Chat Q&A History → At-least-once (with idempotency)
Reason:
- If message lost, user misses a Q&A pair (bad)
- If message duplicate, we detect & skip via message ID (acceptable)
- Transactional exactness not needed (not money-critical)

Configuration:
producer = Producer(acks='all')  # Wait for all in-sync replicas
consumer.enable.auto.commit = False  # Manual commit after processing
consumer.auto.offset.reset = 'earliest'  # Replay if consumer fails
```

---

## F. PRODUCTION, OBSERVABILITY & SECURITY

### Q26: What logging, tracing and metrics would you add to troubleshoot issues in production?

**Answer:**
```python
from opentelemetry import trace, metrics
import logging

# Structured Logging
logger = logging.getLogger(__name__)

@app.websocket("/summarize/{product_id}")
async def summarize_endpoint(product_id, websocket: WebSocket):
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] Client connected", extra={
        "request_id": request_id,
        "product_id": product_id,
        "timestamp": datetime.now().isoformat(),
        "user_agent": websocket.headers.get("user-agent")
    })
    
    try:
        start_time = time.time()
        
        # Log checkpoint 1
        logger.info(f"[{request_id}] Checking DB cache...", extra={
            "step": "db_check",
            "product_id": product_id
        })
        
        summary = get_db_summary(product_id)
        
        if not summary:
            logger.info(f"[{request_id}] Cache miss; generating summary", extra={
                "step": "cache_miss",
                "product_id": product_id
            })
            
            summary = await get_summary(...)
            
            elapsed = time.time() - start_time
            logger.info(f"[{request_id}] Summary generated in {elapsed}s", extra={
                "step": "summary_generated",
                "latency_ms": elapsed * 1000,
                "summary_length": len(summary)
            })
        
        await websocket.send_json({"summary": summary})
        
    except Exception as e:
        logger.error(f"[{request_id}] Error in summarize endpoint", exc_info=True, extra={
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "product_id": product_id,
            "traceback": traceback.format_exc()
        })
        await websocket.close(code=1011, reason="Internal Server Error")

# Metrics (Prometheus)
from prometheus_client import Counter, Histogram, Gauge

# Counter: total requests
summarize_requests = Counter(
    'summarize_requests_total',
    'Total summarize requests',
    ['status']  # label: success, error, cache_hit, cache_miss
)

# Histogram: response latency
summarize_latency = Histogram(
    'summarize_latency_seconds',
    'Summarize endpoint latency',
    buckets=(0.5, 1, 2, 5, 10)
)

# Gauge: active WebSocket connections
websocket_connections = Gauge(
    'websocket_active_connections',
    'Active WebSocket connections'
)

# Usage:
summarize_latency.observe(elapsed)
summarize_requests.labels(status='success').inc()
websocket_connections.inc()

# Distributed Tracing (OpenTelemetry)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("summarize_endpoint") as span:
    span.set_attribute("product_id", product_id)
    span.set_attribute("request_id", request_id)
    
    with tracer.start_as_current_span("get_summary") as child_span:
        summary = await get_summary(...)
        child_span.set_attribute("summary_length", len(summary))

# Dashboards (Grafana)
# - p50, p95, p99 latency over time
# - error rate (errors/total requests)
# - cache hit ratio
# - LLM API spend per hour
# - Active connections; queued requests
# - Error breakdown (timeouts, API errors, etc.)

# Alerts (AlertManager)
# IF (error_rate > 5%) FOR 5min → Page oncall
# IF (p99_latency > 10s) FOR 10min → Warn
# IF (daily_cost > $500) → Alert billing team
```

---

### Q27: What data retention and privacy controls should we implement for uploaded PDFs and generated summaries?

**Answer:**
```
Data Retention Policy:

1. PDF Files
   └─ User can explicitly request deletion
   └─ Auto-delete if not accessed for 90 days (notify user first)
   └─ Never auto-delete if compliance flag set (e.g., legal hold)

2. Summaries
   └─ Keep for 1 year (for audit trail)
   └─ After 1 year, archive to cold storage (Glacier)
   └─ Delete after 7 years (legal requirement)

3. Chat History (Q&A pairs)
   └─ Keep for 6 months (user convenience)
   └─ After 6 months, anonymize (remove user_id)
   └─ Retention: 2 years for audit, then delete

Privacy Controls:

Role-Based Access:
├─ Admin: Can view/export all data
├─ Document Owner: Can view own PDFs/summaries
├─ Team Member: Can view if shared (depends on permissions)
└─ Auditor: Read-only access to logs, no data access

Data Redaction:

class PIIRedacter:
    def redact(self, text):
        # PII patterns to redact before sending to LLM
        patterns = {
            'email': r'[\w\.-]+@[\w\.-]+\.\w+',
            'phone': r'\+?1?\d{9,}\d',
            'ssn': r'\d{3}-\d{2}-\d{4}',
            'credit_card': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
            'api_key': r'[a-zA-Z0-9]{32,}',
        }
        
        for pii_type, pattern in patterns.items():
            text = re.sub(pattern, f'[{pii_type.upper()}]', text)
        
        return text

# Before sending to LLM:
cleaned_text = PIIRedacter().redact(pdf_text)
summary = await get_summary(cleaned_text)

Encryption:

At Rest (S3):
- AES-256 encryption
- Customer-managed keys (AWS KMS)

In Transit:
- TLS 1.2+ for all connections
- Signed URLs for S3 downloads (expire after 1 hour)

Database:
- Encrypt sensitive columns (summaries, chat history)
- Use transparent data encryption (TDE)

Audit Logging:

Log all data access:
{
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": "user_123",
    "action": "downloaded_pdf",  # or view_summary
    "resource_id": "product_456",
    "ip_address": "192.168.1.1",
    "result": "success"
}

Alert on suspicious patterns:
- Same user downloading 1000 PDFs in 1 hour (data exfil)
- Access from unusual geographic location
- Multiple failed auth attempts

User Rights (GDPR/CCPA compliance):

class UserDataManager:
    def export_user_data(self, user_id):
        """Export all user data in machine-readable format."""
        return {
            "pdfs": [self.db.get_pdfs(user_id)],
            "summaries": [self.db.get_summaries(user_id)],
            "chat_history": [self.db.get_chats(user_id)],
            "access_logs": [self.db.get_logs(user_id)]
        }
    
    def delete_user_data(self, user_id):
        """Permanently delete all user data (right to be forgotten)."""
        self.db.execute("DELETE FROM pdfs WHERE user_id = ?", user_id)
        self.db.execute("DELETE FROM summaries WHERE user_id = ?", user_id)
        self.db.execute("DELETE FROM chat_history WHERE user_id = ?", user_id)
        # Keep anonymized logs for 2 years (legal requirement)
        self.db.execute("UPDATE access_logs SET user_id = NULL WHERE user_id = ?", user_id)
```

---

### Q28: How would you design testing (unit, integration, e2e) for components that call external LLMs?

**Answer:**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock

# Unit Test (mock LLM)
@patch('modules.summarize_pdf.llm.ainvoke')
async def test_summarize_pdf(mock_llm_invoke):
    # Mock LLM response
    mock_llm_invoke.return_value = "Test summary"
    
    result = await summarize_pdf("test.pdf")
    
    assert result == "Test summary"
    mock_llm_invoke.assert_called_once()

# Integration Test (real LLM, but with canned prompt/response)
@pytest.fixture
def mock_pdf_content():
    return """
    Company: Acme Inc.
    Founded: 2010
    Revenue: $10M
    """

async def test_summarization_chain(mock_pdf_content):
    """Test the full summarization chain with mock PDF."""
    
    original_get_pdf = get_pdf_file
    
    def mock_get_pdf(product_id):
        return mock_pdf_content  # Return canned content
    
    with patch('modules.summarize_pdf.get_pdf_file', mock_get_pdf):
        summary = await get_summary("test_product_id")
    
    # Assert summary contains key facts, not exact text (LLM may vary)
    assert "Acme" in summary
    assert "2010" in summary or "founded" in summary.lower()

# E2E Test (real API call, but test environment)
@pytest.mark.e2e
async def test_end_to_end_summarize_with_real_llm():
    """Test against real LLM API (staging environment)."""
    
    product_id = "test_e2e_123"
    
    # Create test PDF
    test_pdf_path = "test_data/sample.pdf"
    
    # Call real endpoint
    response = await client.get(f"/summarize/{product_id}")
    
    # Assert response structure
    assert response.status_code == 200
    assert "summary" in response.json()
    
    # Measure latency
    latency = response.elapsed.total_seconds()
    assert latency < 30  # Should complete in <30s
    
    # Verify no PII in response
    pii_patterns = {
        'email': r'[\w\.-]+@[\w\.-]+',
        'ssn': r'\d{3}-\d{2}-\d{4}'
    }
    for pii_type, pattern in pii_patterns.items():
        assert not re.search(pattern, response.json()['summary']), \
            f"PII ({pii_type}) found in response"

# Property-based Testing (Hypothesis)
from hypothesis import given, strategies as st

@given(st.text(min_size=100, max_size=10000))
async def test_summarize_accepts_any_valid_text(text):
    """Test summarization works on any text input."""
    
    try:
        result = await summarize_pdf(text)
        # Should always return a string
        assert isinstance(result, str)
        # Summary should be shorter than input
        assert len(result) < len(text)
    except (InputError, TimeoutError):
        # Acceptable failures
        pass

# Regression Test Suite (maintain over time)
canonical_tests = [
    {
        "name": "Simple contract",
        "input_file": "test_data/contract_simple.pdf",
        "expected_contains": ["parties agree", "consideration"],
        "expected_not_contains": ["hallucinated_clause"]
    },
    {
        "name": "Long technical doc",
        "input_file": "test_data/tech_spec_100pages.pdf",
        "expected_contains": ["architecture", "requirements"],
        "expected_not_contains": ["fake_data"]
    },
    {
        "name": "With PII (should redact)",
        "input_file": "test_data/doc_with_ssn.pdf",
        "expected_not_contains": ["123-45-6789"]
    }
]

@pytest.mark.parametrize("test_case", canonical_tests)
async def test_regression_suite(test_case):
    """Regression tests to prevent quality degradation."""
    
    result = await summarize_pdf(test_case["input_file"])
    
    for expected in test_case["expected_contains"]:
        assert expected.lower() in result.lower(), \
            f"Expected '{expected}' not found in summary"
    
    for not_expected in test_case["expected_not_contains"]:
        assert not_expected.lower() not in result.lower(), \
            f"Unexpected '{not_expected}' found in summary"

# Cost Simulation Test
async def test_cost_estimation():
    """Ensure LLM costs don't spike unexpectedly."""
    
    # Simulate 100 summarizations
    total_cost = 0
    for i in range(100):
        tokens = estimate_tokens("test_doc_300_words.pdf")
        cost = tokens * PRICE_PER_1K_TOKENS
        total_cost += cost
    
    # Assert reasonable budget
    assert total_cost < 50, f"100 summaries cost ${total_cost} (expected <$50)"

# Mock LLM Strategy (for fast tests)
class MockLLM:
    """Fake LLM for testing without API calls."""
    
    def __init__(self):
        self.responses = {
            "summarize": "Mock summary",
            "qa": "Mock answer"
        }
    
    async def ainvoke(self, prompt):
        if "summarize" in prompt.lower():
            return self.responses["summarize"]
        return self.responses["qa"]

# Setup fixtures
@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.fixture
def app_with_mock_llm(mock_llm):
    """Inject mock LLM into app for testing."""
    with patch('modules.chat_module.LLM', mock_llm):
        yield app
```

---

## G. AI CODING, TOOLS, AGENT COMPARISONS

### Q29: If using AI coding assistants (Codex or Claude), what workflow steps would you follow to integrate generated code safely?

**Answer:**
```
Workflow: AI-Generated Code → Production

Step 1: Code Generation (AI Assistant prompt)
┌─────────────────────────────────────┐
│ Prompt to Claude/Copilot/Codex:     │
│ - Clear task description            │
│ - Existing code patterns            │
│ - Type hints expected                │
│ - Error handling requirements       │
└─────────────────────────────────────┘
  ↓
Step 2: Initial Review (15 min)
├─ Does it match requirements?
├─ Are there obvious syntax errors?
├─ Any security issues (SQL injection, hardcoded secrets)?
└─ Is error handling present?

Step 3: Test Suite Creation (30 min)
├─ Unit tests for happy path
├─ Edge case tests (None, empty, large input)
├─ Integration tests with mocked dependencies
└─ Jest/pytest coverage target: >80%

Step 4: Local Validation
├─ Run linter (pylint, mypy for type checking)
├─ Check formatting (black, isort)
├─ Run security scanner (bandit, Safety)
└─ Ensure all tests pass

Step 5: Code Review (peer review, 30-60 min)
├─ Readability: Is it understandable?
├─ Performance: Any O(n²) loops or memory leaks?
├─ Maintainability: Would future devs understand this?
├─ AI-specific checks:
│  ├─ Are there hallucinations? (claims without proof)
│  ├─ Does it duplicate existing code?
│  └─ Are comments accurate?
└─ Approval required before merge

Step 6: Staging Deployment (1-2 hours)
├─ Deploy to staging environment
├─ Run full test suite (unit + integration + e2e)
├─ Performance testing (latency, memory profiling)
├─ Load testing (if async code)
└─ Manual QA: smoke test the feature

Step 7: Canary Release (production, 5%)
├─ Deploy to 5% of production traffic
├─ Monitor:
│  ├─ Error rate (target: <0.1%)
│  ├─ Latency (target: no >20% increase)
│  ├─ Resource usage
│  └─ Business metrics
├─ Alert on thresholds
└─ Rollback if issues detected

Step 8: Full Release (100%)
├─ If canary healthy for 24 hours → full release
├─ Monitor closely first week
└─ Keep rollback plan ready

Code Quality Checklist (automated):
✓ Linting passes
✓ Type checking passes (mypy)
✓ Security scan passes (bandit)
✓ Test coverage >80%
✓ No hardcoded credentials or API keys
✓ No SQL injection vulnerabilities
✓ No shell injection vulnerabilities
✓ Docstrings/comments for complex logic
✓ Error handling for all exceptions
✓ Logging at key checkpoints
```

**Example (Python)**:
```python
# Generated by Claude + enhanced by human

async def process_user_pdf(user_id: str, product_id: str) -> dict:
    """
    Process PDF for user and generate summary.
    
    Args:
        user_id: User identifier
        product_id: Product identifier
        
    Returns:
        dict with summary and metadata
        
    Raises:
        ValueError: If user_id or product_id invalid
        PDFProcessingError: If PDF parsing fails
    """
    # Input validation (human added)
    if not user_id or not isinstance(user_id, str):
        raise ValueError("Invalid user_id")
    
    try:
        # Generated code
        pdf_path = get_pdf_file(product_id)
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        
        # Enhanced with logging (human added)
        logger.info(f"Loaded PDF: pages={len(docs)}", extra={"user_id": user_id})
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=500
        )
        texts = text_splitter.split_documents(docs)
        
        summary = await generate_summary(texts)
        
        # Added validation (human added)
        if not summary or len(summary) < 10:
            raise ValueError("Summary generation failed")
        
        return {"summary": summary, "status": "success"}
    
    except Exception as e:
        logger.error(
            "PDF processing failed", 
            exc_info=True, 
            extra={"user_id": user_id, "product_id": product_id}
        )
        raise PDFProcessingError(f"Failed to process PDF: {str(e)}")

# Test (human wrote)
@pytest.mark.asyncio
async def test_process_user_pdf():
    with patch('modules.summarize_pdf.get_pdf_file') as mock_get:
        mock_get.return_value = "test.pdf"
        
        result = await process_user_pdf("user_1", "product_1")
        
        assert result["status"] == "success"
        assert len(result["summary"]) > 0

# Code review comment (human):
# ✅ Generated code looks good
# ✅ Type hints present
# ⚠️ Added logging (missing in generated version)
# ⚠️ Added input validation (missing in generated version)
# ✅ Error handling good
```

---

### Q30: What are the key differences between 'Codex-style' code generation and 'Claude-style' reasoning/agent approaches?

**Answer:**

| Aspect | Codex | Claude |
|--------|-------|--------|
| **Training** | Code-specific (GitHub, StackOverflow) | General text + code (books, docs, code) |
| **Approach** | Pattern matching on similar code | Reasoning + multi-step planning |
| **Strength** | Quick boilerplate, standard patterns | Complex logic, novel solutions |
| **Output** | Deterministic code snippets | Explanations + code + reasoning |
| **Speed** | Faster (direct generation) | Slower (thinks through problem) |

**Codex Style** (GPT, GitHub Copilot):
```python
# Prompt: "Complete this function"
def fibonacci(n):
    if n <= 1:
        return n
    return fib  # Copilot auto-completes

# Output (instant):
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Pro: Fast, works for common patterns
# Con: Doesn't optimize (exponential complexity); no explanation
```

**Claude Style** (Claude, Chain-of-Thought):
```
# Prompt: "Write efficient fibonacci function with explanation"

Claude Response:
"Let me think about this step-by-step:
1. Recursive fibonacci is O(2^n) - too slow
2. Dynamic programming with memoization is O(n)
3. Or iterative approach with O(1) space

Here's the optimized solution:

def fibonacci(n):
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b  # Iterative O(n) time, O(1) space

Why this approach: Avoids redundant calculations"

# Pro: Explains reasoning; optimizes; considers trade-offs
# Con: Slower; longer response
```

**When to Use Each**:
- **Codex**: Quick boilerplate (CRUD endpoints, data validation)
- **Claude**: Complex algorithms, design decisions, refactoring advice

---

### Q31: When would you use an "extension agent" pattern vs direct LLM calls for application logic?

**Answer:**

| Scenario | Direct LLM | Agent |
|----------|-----------|-------|
| **Task Complexity** | Simple (1-2 steps) | Complex (multi-step reasoning) |
| **Tool Use** | No | Yes (DB, API, file ops) |
| **Determinism Needed** | Less critical | Very critical |
| **Examples** | Summarize, classify | "Find all late invoices and send reminder" |

**Direct LLM Call** (when query is simple):
```python
async def classify_document(text):
    """Classify doc as 'legal', 'financial', 'other'."""
    prompt = f"Classify: {text}"
    result = await llm.ainvoke(prompt)  # Single call; done
    return result.strip()

# Usage
doc_type = await classify_document("Contract of sale...")
```

**Agent Pattern** (when task needs tools):
```python
from langchain.agents import initialize_agent, Tool
from langchain.tools import tool

# Define tools
@tool
def query_invoice_db(status: str) -> list:
    """Find invoices by status (late, paid, pending)."""
    return db.query(f"SELECT * FROM invoices WHERE status = '{status}'")

@tool
def send_email(to: str, subject: str, body: str) -> dict:
    """Send email notification."""
    # Send via SMTP
    return {"status": "sent"}

tools = [
    Tool(name="Query Invoices", func=query_invoice_db),
    Tool(name="Send Email", func=send_email)
]

# Create agent
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

# Complex task: "Find late invoices and email customers"
result = await agent.arun(
    """
    Find all invoices with status 'late'.
    For each, send an email reminder to the customer
    with subject "Payment Reminder" and body "Your payment is overdue."
    """
)
```

**Why Agent for complex task**:
1. LLM reasons: "I need to query the database first"
2. Calls tool: `query_invoice_db('late')`
3. Gets result: [invoice_1, invoice_2, ...]
4. Reasons: "Now send emails"
5. Calls tool: `send_email(customer_1@..., "Payment Reminder", "...")`
6. Reasons: "Done with all invoices"

---

### Q32: How should prompts, tool-use, and state be structured when building an agent that executes steps?

**Answer:**
```python
from pydantic import BaseModel
from typing import Optional
import json

# Define Agent State
class AgentState(BaseModel):
    """State maintained across agent steps."""
    task_id: str
    goal: str
    step: int
    completed_actions: list[str]
    context: dict  # Preserve info from previous steps
    error: Optional[str] = None
    
    def log_action(self, action: str, result: dict):
        """Record action for audit trail."""
        self.completed_actions.append({
            "step": self.step,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.step += 1

# Define Tool Contracts (strict I/O)
class ToolResult(BaseModel):
    """Tool result must be parsable."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

class QueryInvoicesTool:
    def schema(self):
        return {
            "name": "query_invoices",
            "description": "Find invoices by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["late", "paid", "pending"]},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["status"]
            }
        }
    
    def execute(self, status: str, limit: int = 10) -> ToolResult:
        try:
            invoices = db.query(f"SELECT * FROM invoices WHERE status = ? LIMIT ?", 
                               status, limit)
            return ToolResult(success=True, data={"invoices": invoices})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

# Structured Prompt for Agent
AGENT_SYSTEM_PROMPT = """
You are a task-execution agent. Your goal is to complete multi-step tasks using available tools.

Rules:
1. Break down the goal into steps
2. Use tools to perform actions
3. Validate tool outputs before proceeding
4. If tool fails, try alternative approach or report error
5. Always explain your reasoning
6. Track completed steps

Available tools:
{tools_list}

Respond in JSON with this format:
{
    "reasoning": "Why are you taking this action?",
    "next_action": "query_invoices",
    "parameters": {"status": "late"},
    "expected_outcome": "Get list of overdue invoices"
}
"""

# Agent Orchestration
class TaskAgent:
    def __init__(self):
        self.tools = {
            "query_invoices": QueryInvoicesTool(),
            "send_email": SendEmailTool(),
            "log_action": LogActionTool()
        }
    
    async def execute_task(self, goal: str) -> dict:
        state = AgentState(
            task_id=str(uuid.uuid4()),
            goal=goal,
            step=0,
            completed_actions=[]
        )
        
        logger.info(f"Starting task: {goal}", extra={"task_id": state.task_id})
        
        max_steps = 10
        while state.step < max_steps:
            # Get next action from LLM
            prompt = f"""
            Goal: {state.goal}
            Current step: {state.step}
            Completed actions: {json.dumps(state.completed_actions, default=str)}
            Current context: {json.dumps(state.context)}
            
            What's your next action?
            """
            
            response = await llm.ainvoke(
                prompt,
                temperature=0.2  # Deterministic
            )
            
            try:
                action_plan = json.loads(response)
            except json.JSONDecodeError:
                state.error = f"LLM response not JSON: {response}"
                break
            
            # Validate action
            action_name = action_plan.get("next_action")
            if action_name not in self.tools:
                state.error = f"Unknown action: {action_name}"
                break
            
            # Execute tool
            try:
                tool = self.tools[action_name]
                result = tool.execute(**action_plan.get("parameters", {}))
                
                state.log_action(action_name, result.dict())
                
                if result.success:
                    state.context.update(result.data or {})
                else:
                    state.error = result.error
                    break
                
                # Check if done
                if action_plan.get("is_final"):
                    break
            
            except Exception as e:
                state.error = str(e)
                logger.error(f"Tool execution failed", exc_info=True, 
                            extra={"task_id": state.task_id})
                break
        
        logger.info(f"Task complete", extra={
            "task_id": state.task_id,
            "steps": state.step,
            "status": "success" if not state.error else "failed",
            "error": state.error
        })
        
        return state.dict()

# Usage
agent = TaskAgent()
result = await agent.execute_task(
    "Find all late invoices and send reminder emails to customers"
)
print(result)
```

**Best Practices**:
1. **State**: Store context between steps (JSON serializable)
2. **Prompts**: Be explicit about available actions
3. **Tools**: Define strict schemas; validate inputs/outputs
4. **Error Handling**: Backoff + retry; log detailed traces
5. **Monitoring**: Track step execution time; alert if stuck

---

### Q33: What code review and validation steps would you enforce for AI-generated code before merging to main?

**Answer:**
```
Mandatory Code Review Checklist (Git pre-merge hook):

1. STATIC ANALYSIS (automated)
   ├─ Linting (pylint, ESLint)
   │  └─ No style errors
   ├─ Type Checking (mypy, TypeScript)
   │  └─ No type mismatches
   ├─ Security Scan (Bandit, OWASP)
   │  ├─ No hardcoded secrets
   │  ├─ No SQL injection
   │  ├─ No shell execution
   │  └─ No insecure deserialization
   ├─ Complexity Check
   │  ├─ Cyclomatic complexity < 10
   │  ├─ Function length < 50 lines
   │  └─ No deeply nested logic
   └─ Dependency Audit
      ├─ No new unvetted dependencies
      └─ Known vulnerable deps flagged

2. TEST COVERAGE (automated)
   ├─ Minimum 80% code coverage
   ├─ All branches tested (if/else, try/catch)
   ├─ Unit tests pass
   ├─ Integration tests pass
   └─ E2E tests pass

3. PERFORMANCE CHECK (automated)
   ├─ No performance regression (vs baseline)
   ├─ Benchmark tests < expected latency
   ├─ Memory leak check (if applicable)
   └─ Load test for concurrent operations

4. HUMAN REVIEW (AI-generated code)
   Author: Copilot/Claude/Codex
   Reviewer: Human (required)
   
   Checklist:
   ☐ Code matches requirements exactly
   ☐ No obvious bugs or logic errors
   ☐ Consistent with codebase style
   ☐ Includes proper error handling
   ☐ Includes logging at critical points
   ☐ No security vulnerabilities
   ☐ Docstrings/comments clear and accurate
   ☐ No code duplication (checked via SonarQube)
   ☐ Database queries optimized (no N+1)
   ☐ No hallucinations (claims without evidence)
   
   for PR comment:
   "Code generated by {AI tool}. Please verify:
    - Logic correctness
    - Security review
    - Performance implications"

5. AI-SPECIFIC VALIDATION (for LLM-generated code)
   ├─ Hallucination Check
   │  └─ Does code claim functions/classes that don't exist?
   ├─ Source Attribution
   │  └─ If code looks copied, verify license compatibility
   ├─ External Dependency Check
   │  └─ All imports available in requirements.txt?
   └─ Determinism Check
   │  └─ Non-deterministic operations (e.g., timing) justified?

6. COMPLIANCE & LICENSING
   ├─ No GPL code in proprietary repo
   ├─ No GPL-ed open source without disclosure
   ├─ Proper attribution for third-party code
   └─ No LGPL conflicts

Enforcement Tool (example):

# .github/workflows/ai-code-review.yml
name: AI-Generated Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    if: contains(github.body, 'Generated by')  # PR mentions AI generation
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Pylint
        run: pylint src/ --fail-under=8.0
      
      - name: Run MyPy
        run: mypy src/ --strict
      
      - name: Security Scan (Bandit)
        run: bandit -r src/ -f json -o bandit-report.json
      
      - name: Test Coverage
        run: pytest --cov=src/ --cov-fail-under=80
      
      - name: Performance Test
        run: pytest benchmarks/ -v
      
      - name: Hold for Human Review
        run: |
          echo "This PR contains AI-generated code."
          echo "Requires manual review before merge."
          exit 1  # Block merge; reviewer must approve

      - name: Require Approval from 2 reviewers
        uses: actions/github-script@v6
        with:
          script: |
            const pr = context.payload.pull_request;
            const reviews = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: pr.number
            });
            const approvals = reviews.filter(r => r.state === 'APPROVED');
            if (approvals.length < 2) {
              throw new Error('AI-generated code requires 2 approvals');
            }

Tracking AI-Generated Code:

# In code:
"""
Generated by: Claude (2024-01-15)
Prompt: "Write async PDF summarizer with Chroma embeddings"
PR: #1234
Reviewer:Approved by @alice @bob
"""

# Metrics:
- Track % of codebase generated by AI
- Track defect rate (bugs per 1000 lines)
- Compare vs human-written code
- Adjust review rigor based on recent failures
```

---

### Q34: What are the primary "do's and don'ts" when relying on AI coding tools in production?

**Answer:**

## DO'S ✅

1. **DO** Use AI for boilerplate (CRUD, data validation)
   ```python
   # Good: Repetitive, low-risk code
   def validate_email(email: str) -> bool:
       return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))
   ```

2. **DO** Have humans review all AI code before merge
   - Code review is non-negotiable
   - Even great AI makes mistakes

3. **DO** Write comprehensive tests
   - Unit tests (mock dependencies)
   - Integration tests (with real services)
   - E2E tests (realistic scenarios)

4. **DO** Use LLMs for planning/architecture (reasoning)
   - Claude is good at "design this system"
   - Use output to inform code design

5. **DO** Provide clear, detailed prompts
   ```python
   # Good prompt
   """
   Write an async function to fetch invoices from PostgreSQL.
   - Use connection pooling
   - Add error handling with retries
   - Return dict with ['invoices', 'count', 'error']
   - Use type hints
   - Log at INFO level
   """
   
   # Bad prompt
   "Write invoice fetching code"
   ```

6. **DO** Version and track AI-generated code
   - Tag commits: "Generated by Claude v1"
   - Useful for comparing quality over time

7. **DO** Use deterministic parameters
   ```python
   # Good: Reproducible
   response = llm.invoke(prompt, temperature=0.2, max_tokens=500)
   
   # Bad: Non-deterministic
   response = llm.invoke(prompt)  # Defaults vary
   ```

8. **DO** Monitor production metrics
   - Alert if using AI-generated code causes errors
   - Rollback ability if issues detected

---

## DON'Ts ❌

1. **DON'T** Use AI for security-critical code without deep review
   ```python
   # Bad: Don't blindly trust AI for auth
   def verify_token(token):  # Generated by AI
       return token == stored_token  # Timing attack!
   ```
   
   **Fix**: Manual review + security audit

2. **DON'T** Commit AI code without tests
   - No tests = high risk of production bugs
   - Target: 80%+ coverage

3. **DON'T** Ignore hallucinations
   - AI might generate functions/APIs that don't exist
   - Always verify external dependencies exist

4. **DON'T** Deploy AI code directly to production
   - Always: Dev → Staging → Canary (5%) → Full release
   - Never: Enable "auto-merge" for AI-generated PRs

5. **DON'T** Leak sensitive data in prompts
   ```python
   # Bad: Sending real data to 3rd-party LLM
   response = llm.invoke(f"Summarize this: {real_customer_data}")
   
   # Good: Use synthetic/redacted data
   response = llm.invoke(f"Summarize this: {redacted_data}")
   ```

6. **DON'T** Over-rely on AI for complex business logic
   ```python
   # Bad: A/B testing algorithm from AI
   def calculate_required_sample_size():  # Generated
       # Might be mathematically wrong
   
   # Good: Use peer-reviewed libraries
   from statsmodels.stats.power import tt_solve_power
   ```

7. **DON'T** Skip version control
   - Don't use AI in production without git history
   - Need to rollback if needed

8. **DON'T** Ignore future maintenance burden
   - AI code might be harder for humans to maintain
   - Especially if no docstrings/comments
   - Plan for knowledge transfer

---

## Production Readiness Checklist

```
Before deploying AI-generated code:

✅ Code passes all automated checks
   ├─ Linting
   ├─ Type checking
   ├─ Security scan
   └─ Tests cover 80%+ branches

✅ Human review completed
   ├─ 2+ approvals for critical code
   ├─ Security review done
   └─ Performance review done

✅ Documentation
   ├─ Docstrings present
   ├─ Complex logic explained
   └─ Any assumptions documented

✅ Monitoring in place
   ├─ Error rate alerts
   ├─ Performance baseline
   └─ Rollback/kill switch tested

✅ Staged rollout plan
   ├─ Staging validation
   ├─ Canary 5% plan
   └─ Rollback procedure

Only then: Deploy to production
```

---

# PART 2: PROMPTING GUIDELINES — DETAILED IMPLEMENTATION

## Comprehensive Prompting Strategy

### Purpose & Core Principles Recap
- **Make prompts reliable**: Same input → consistent output
- **Reduce hallucinations**: Ground responses in facts
- **Standardize format**: Repeatable; easy to validate

### Prompting Best Practices (Deep Dive)

#### 1. System Instruction Design

```python
# Weak system instruction
system = "You are a helpful assistant."

# Strong system instruction
system = """
You are a document analysis specialist for legal/financial documents.
Your role: Extract key information accurately.
Your constraints:
- Only use facts explicitly stated in the document
- If information isn't available, respond: "NOT_STATED"
- Never infer or speculate
- Maintain professional neutral tone
- Flag any unclear or ambiguous text
Output format: You will respond in structured JSON with specific fields.
"""
```

#### 2. Few-Shot Prompting (Teaching by Example)

```python
prompt = """
Classify this document type as: CONTRACT | INVOICE | REPORT | OTHER

Example 1:
Input: "Agreement between Company A and Company B..."
Output: {"type": "CONTRACT", "confidence": "HIGH"}

Example 2:
Input: "Invoice #12345, Date: 2024-01-15, Amount: $1,000"
Output: {"type": "INVOICE", "confidence": "HIGH"}

Now classify this:
Input: {document_text}
Output:
"""
```

#### 3. Chain-of-Thought Prompting (Reasoning Steps)

```python
prompt = """
Let's think step by step:
1. Identify the main parties involved
2. Find the key obligations
3. Note any conditions or contingencies
4. Extract dates and amounts
5. Summarize the agreement

Document:
{full_document_text}

Response format: JSON with {parties, obligations, conditions, dates, amounts, summary}
"""
```

#### 4. Output Schema Enforcement

```python
prompt = """
Respond ONLY in this JSON format. No other text:
{
  "summary": "string | max 250 words",
  "key_points": "array of strings | 3-5 points",
  "risk_level": "HIGH | MEDIUM | LOW",
  "confidence": "0.0-1.0 | Your confidence in this analysis",
  "needs_review": "boolean | Flag if ambiguous or suspicious",
  "sources": "array | Which sentences support this?"
}
"""
```

#### 5. Temperature & Parameter Tuning

```python
# For deterministic outputs (fact extraction)
response = llm.invoke(
    prompt,
    temperature=0.0,  # Always same response
    top_p=0.95,
    max_tokens=500,
    frequency_penalty=0.5,  # Avoid repetition
)

# For creative outputs
response = llm.invoke(
    prompt,
    temperature=0.7,  # Some variation
    max_tokens=1000
)
```

#### 6. Guardrails & Error Handling

```python
# Tell model how to handle uncertain cases
prompt = """
If you cannot extract the information due to:
- Document in wrong format → Respond: {"error": "INVALID_FORMAT"}
- Information unclear → Respond: {"status": "UNCLEAR", "clarification_needed": "..."}
- Document too short → Respond: {"error": "INSUFFICIENT_DATA"}

Otherwise, respond with the requested structure.
"""
```

### Real Implementation Examples

**Example 1: Contract Summarization**

```python
async def summarize_contract(contract_text: str) -> dict:
    """Summarize legal contract with structured output."""
    
    system_prompt = """
    You are a legal document analyst. Your job: 
    Extract key contract terms accurately. 
    Never add interpretations; stick to facts.
    Output JSON only.
    """
    
    user_prompt = f"""
    Analyze this contract and extract key information:
    
    CONTRACT:
    {contract_text}
    
    Respond in JSON format:
    {{
        "parties": ["list of involved parties"],
        "term": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
        "key_obligations": {{"party_1": "obligation_1", "party_2": "obligation_2"}},
        "payment_terms": {{"amount": "number", "currency": "string", "schedule": "string"}},
        "termination_clause": "how contract can be terminated",
        "confidentiality": boolean,
        "risk_level": "HIGH | MEDIUM | LOW",
        "needs_review": boolean,
        "reason_for_review": "optional explanation"
    }}
    """
    
    response = await llm.ainvoke(
        user_prompt,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "raw": response}
```

**Example 2: Multi-Step Agent Prompting**

```python
async def execute_document_workflow(doc_id: str) -> dict:
    """
    Multi-step process:
    1. Classify document
    2. Extract key info
    3. Determine next action
    """
    
    doc = get_document(doc_id)
    
    # Step 1: Classify
    classification = await classify_document(doc)
    
    if classification['type'] == 'CONTRACT':
        # Step 2: Extract contract details
        details = await summarize_contract(doc)
        
        # Step 3: Recommend action
        action_prompt = f"""
        Based on this contract analysis, what's the recommended next step?
        
        Analysis: {json.dumps(details)}
        
        Options:
        - REVIEW: Needs legal review
        - APPROVE: Looks standard
        - NEGOTIATE: Has risky terms
        - REJECT: Unacceptable terms
        
        Recommend: (one of above)
        Reason: (2-3 sentences)
        """
        
        recommendation = await llm.ainvoke(action_prompt)
        return {
            "doc_id": doc_id,
            "classification": classification,
            "details": details,
            "next_action": recommendation
        }

```

**Example 3: Handling Ambiguity**

```python
async def extract_payment_terms(invoice_text: str) -> dict:
    """Extract payment terms; handle ambiguity gracefully."""
    
    prompt = f"""
    Extract payment terms from this invoice. 
    Be precise; don't guess.
    
    INVOICE:
    {invoice_text}
    
    Respond in JSON:
    {{
        "amount": {{"value": float, "currency": "string"}},
        "due_date": "YYYY-MM-DD or 'UNKNOWN' if missing",
        "payment_method": "method or 'NOT_STATED'",
        "discount": {{"percentage": float, "condition": "string"}},
        "confidence": 0.0-1.0,
        "ambiguities": ["list of unclear items"],
        "requires_clarification": boolean
    }}
    
    For unknown fields, use 'UNKNOWN' or 'NOT_STATED'.
    Never invent information.
    """
    
    response = await llm.ainvoke(prompt, temperature=0.1)
    
    parsed = json.loads(response)
    
    # Validate confidence
    if parsed['confidence'] < 0.7:
        logger.warning(f"Low confidence extraction: {parsed}")
        # Alert user or route to manual review
    
    return parsed
```

---

## Testing & Validation Prompts

### Regression Test Suite

```python
test_cases = [
    {
        "name": "Simple invoice",
        "input": "Invoice # INV-001... Date: 2024-01-15... Amount: $500",
        "expected": {
            "amount": 500,
            "currency": "USD",
            "date_pattern": "2024-01-15"
        },
        "threshold": "Must extract all 3 fields correctly"
    },
    {
        "name": "Ambiguous date",
        "input": "Invoice dated 01/02/03 for $100",
        "expected": {
            "date_status": "AMBIGUOUS",
            "amount": 100
        },
        "threshold": "Must flag date as ambiguous, not guess"
    },
    {
        "name": "PII in contract",
        "input": "Mr. John Doe (SSN: 123-45-6789) signs contract...",
        "expected": {
            "pii_detected": True,
            "ssn_in_summary": False  # Should be redacted
        },
        "threshold": "Must not expose PII in summary"
    }
]

async def run_regression_tests():
    for test in test_cases:
        result = await extract_info(test["input"])
        
        # Validate
        for key, expected_value in test["expected"].items():
            actual = result.get(key)
            if "pattern" in key:
                assert re.match(expected_value, str(actual))
            else:
                assert actual == expected_value, \
                    f"Test {test['name']} failed: {key}={actual}, expected {expected_value}"
        
        logger.info(f"✓ {test['name']}")

```

---

## Production Monitoring

### Prompt Performance Dashboard

```
Metrics to track:
- Token usage per prompt (cost)
- Response latency (p50, p95, p99)
- Hallucination rate (manual review %)
- User satisfaction (thumbs up/down rate)
- Error rate (malformed responses)
- Confidence score distribution

Alerts:
- If cost per request > baseline × 1.5 → Investigate
- If hallucination rate > 5% → Review prompts
- If latency p99 > 10s → Check LLM load
- If error rate > 1% → Rollback or fix
```

---

## Version Control & Change Management

```
Prompt versioning:

# prompts/summarizer_v2.1.yaml
name: "PDF Summarizer"
version: "2.1"
created_date: "2024-01-15"
author: "Alice"
description: "Multi-step summarization with hallucination guardrails"

prompt: |
  You are a document summarizer...
  [Full prompt text]

parameters:
  temperature: 0.2
  max_tokens: 500
  
test_cases:
  - input: "sample.pdf"
    expected: "key_points_exist"
    
changelog:
  v2.1: "Added PII redaction check"
  v2.0: "Changed output format to JSON"
  v1.0: "Initial release"
```

---

This completes the comprehensive interview preparation guide with:
- ✅ 34 detailed interview answers
- ✅ Real code examples
- ✅ Production-ready implementations
- ✅ Decision frameworks
- ✅ Prompting best practices
- ✅ Testing & validation strategies
- ✅ Monitoring & production tips

**Usage**: Review 2-3 answers daily; practice explaining to a colleague; adjust based on interviewer depth questions.
