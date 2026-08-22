## Context

See `proposal.md` for motivation. Currently, the project is a lightweight Node.js/VanillaJS application with mocked data and hardcoded heuristics. To support true RAG, dynamic agentic workflows, and cloud operations, the architecture must transition to a robust, scalable structure capable of interacting with Vector Databases and the Liara API securely.

## Goals / Non-Goals

**Goals:**
- Replace heuristic routing with a formal Agent framework (e.g., LangGraph or custom ReAct).
- Introduce a local Vector DB for semantic search.
- Modernize the frontend for streaming interactions using Next.js/React.

**Non-Goals:**
- Hosting a standalone Vector DB outside of Liara's PaaS environment (we will use a disk-mounted local instance).
- Modifying Liara's core API (we are purely a consumer of it).

## Decisions

### 1. Framework Selection for Agent Workflow
- **Decision:** Use a Python-based backend (FastAPI) paired with LangGraph.
- **Rationale:** Python has the most robust ecosystem for LLMs and Vector Search (LangChain, LlamaIndex, Qdrant). LangGraph provides the necessary state management for complex, multi-step agent reasoning.
- **Alternatives Considered:** Node.js with LangChain.js. While feasible, Python's data science and NLP libraries are more mature, particularly for data ingestion and chunking of markdown documentation.

### 2. Vector Database
- **Decision:** Use Qdrant locally (via file storage) or ChromaDB mounted on a Liara persistent disk.
- **Rationale:** Both allow for embedded usage without the need for a separate database service, keeping deployment simple and cost-effective on Liara.
- **Alternatives Considered:** Pinecone or Weaviate. Rejected due to the goal of keeping the solution self-contained and avoiding external cloud dependencies/costs.

### 3. Frontend Architecture
- **Decision:** Next.js (App Router) with Tailwind CSS and Server-Sent Events (SSE) for streaming.
- **Rationale:** Next.js provides excellent developer experience and built-in API routes. SSE is more firewall-friendly than WebSockets, which is ideal for deployment on PaaS.
- **Alternatives Considered:** Keeping Vanilla JS. Rejected as managing complex state (streaming chunks, tool calls, and UI updates) becomes unwieldy.

## Risks / Trade-offs

- **Risk:** High memory usage from the local Vector DB and LLM orchestrator running on a single PaaS instance.
  - **Mitigation:** Optimize chunking strategies, use efficient embedding models (e.g., `all-MiniLM-L6-v2`), and monitor Liara resource usage.
- **Risk:** Security of Liara API Tokens.
  - **Mitigation:** Tokens will only be stored in memory during the active session or in encrypted HTTP-only cookies, never persisted in the database or logs.

## Migration Plan

1. Scaffold the Next.js frontend and replace the existing `public/` directory.
2. Develop the FastAPI backend and configure the Vector DB locally.
3. Update `liara.json` and `Dockerfile` for a multi-stage or split deployment if necessary (e.g., using Liara's Docker PaaS for the unified app).