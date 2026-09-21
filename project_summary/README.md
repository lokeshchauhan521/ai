# Project Summary: AI Analysis Service

## Overview
This repository provides an AI-powered PDF analysis and chat service built with FastAPI and WebSockets. Key capabilities:
- Real-time PDF summarization via WebSocket (`/summarize/{product_id}`).
- Interactive Q&A chat over WebSocket (`/recieve-msg/{user_id}/{product_id}`) backed by retrieval-augmented generation using Chroma embeddings and an LLM.
- Asynchronous summarization pipeline using LangChain chains.
- Messaging integration with Kafka for producing/consuming chat QA pairs.
- Embeddings persisted locally (`chroma_files/<product_id>`) and synced to S3 for reuse.
- Cached summaries and DB-backed persistence for summaries.

## Key Components
- `app/app.py`: FastAPI app and WebSocket endpoints. Orchestrates summarize and chat flows.
- `app/routing/routing.py`: Route registration for REST-style resources (uses `services.file_summary`).
- `app/modules/summarize_pdf.py`: Functions to split PDFs and produce concise summaries using an LLM chain.
- `app/modules/chat_module.py`: Handles retrieval (Chroma) or summary-based answering, produces Kafka messages with Q/A.
- `app/modules/produce_messages.py`: Kafka producer helper.
- `app/modules/consume_message.py`: Kafka consumer that filters messages by topic key and yields them for WebSocket clients.
- `app/services/*`: Higher-level request handlers (e.g., `file_summary`).
- `app/utils/*`: Helpers for S3, Redis, DB, logging, file utilities and constants.

## High-level Flow
- Summarize flow:
  1. Client opens WebSocket to `/summarize/{product_id}`.
  2. Server checks DB cache (`get_db_summary`). If present, optionally regenerates.
  3. If missing, `get_pdf_file` locates the PDF file; `modules.summarize_pdf.get_summary` creates summary via LangChain.
  4. Summary saved to DB (`insert_db_summary`) and sent back to client over WebSocket.

- Chat / Q&A flow:
  1. Client opens WebSocket to `/recieve-msg/{user_id}/{product_id}`.
  2. Server listens to Kafka topic (via `consume_message`) and forwards matching messages to the client.
  3. When client sends a question, `modules.chat_module.produce_and_generate_answer` runs:
     - Decides whether to use a document summary or retrieval over embedded documents.
     - If retrieval: ensure Chroma store exists (download from S3 or create from PDF), run RetrievalQA with `LLM`.
     - Produce the QA pair to Kafka via `produce_message`.
  4. Produced Kafka messages are consumed by `consume_message` and forwarded to listening WebSocket clients filtered by topic key.

## Data Stores and Integrations
- Kafka: message bus for Q/A messages (`produce_messages` and `consume_message`).
- S3: stores embedding directories for reuse (`upload_folder_to_s3`, `download_folder_from_s3`).
- Chroma: local vector store persisted under `chroma_files/<product_id>`.
- DB: stores generated summaries (`db_utils`).
- Redis: optional caching layer for summaries (`redis_utils`).

## Operational Notes
- LLM and embeddings are provided via `utils.constants` (`LLM`, `OpenAIEmbeddings`, etc.).
- Logs are written using `utils.logger.FileLogs`.
- WebSockets must handle disconnects and cleanup (`cleanup_space`).
- Kafka config uses `BOOTSTRAP_SERVER` from `utils.constants`.

## Mermaid Flowchart
```mermaid
flowchart LR
  Client[Client (browser)]

  subgraph SummarizeFlow
    %% PDF Summarization
    Client -->|WebSocket /summarize/{product_id}| WebsocketSumm[WebSocket Server]
    WebsocketSumm --> DB[Database: summaries]
    DB -->|exists?| WebsocketSumm
    WebsocketSumm -->|fetch PDF| FileSys[Local PDF storage]
    FileSys --> Summarizer[Summarize Service (modules/summarize_pdf)]
    Summarizer --> DB
    Summarizer --> WebsocketSumm
  end

  subgraph ChatFlow
    %% Interactive Chat / Q&A
    Client -->|WebSocket /recieve-msg/{user_id}/{product_id}| WebsocketChat[WebSocket Server]
    WebsocketChat -->|receive question| ChatModule[Chat Module (modules/chat_module)]
    ChatModule -->|uses| Chroma[Chroma Vector Store]
    Chroma -->|persist/restore| S3[S3 Embedding Storage]
    ChatModule -->|calls| LLM[LLM (utils.constants.LLM)]
    ChatModule -->|produce| KafkaProducer[Kafka Producer]
    KafkaProducer --> KafkaTopic[Kafka Topic]
    KafkaTopic -->|consume| KafkaConsumer[Kafka Consumer (modules/consume_message)]
    KafkaConsumer --> WebsocketChat
    ChatModule --> DB
    ChatModule --> Redis[Redis (cache)]
  end

  style SummarizeFlow fill:#f9f,stroke:#333,stroke-width:1px
  style ChatFlow fill:#ff9,stroke:#333,stroke-width:1px
```

## Files Created
- `project_summary/README.md` (this file)

## Next Steps / Suggestions
- Add architecture diagram image export if needed (render Mermaid to PNG/SVG).
- Add short developer README with setup steps and environment variables (`.env` keys for Kafka, S3, LLM, DB).

---
Generated from code inspection of `app/` modules. If you want, I can also generate a PNG of the Mermaid diagram or add a `project_summary/ARCHITECTURE.md` with endpoint examples. 
