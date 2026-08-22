## 1. Project Scaffolding & Setup

- [ ] 1.1 Scaffold the new Next.js frontend app and verify it boots with `npm run dev`
- [ ] 1.2 Scaffold the FastAPI backend and verify the `/health` endpoint returns a 200 OK status
- [ ] 1.3 Initialize the local Vector DB (e.g., Qdrant/Chroma) and verify connection from the Python backend

## 2. Agent & Workflow Implementation

- [ ] 2.1 Develop the Markdown ingestion script and verify that it chunks and stores Liara Docs in the Vector DB
- [ ] 2.2 Implement the Hybrid Search (Dense + BM25) query logic and verify accurate retrieval of specific keywords
- [ ] 2.3 Implement the LangGraph routing agent and verify it correctly routes mock "error logs" vs "general questions"
- [ ] 2.4 Create the Liara API tools (Deploy, Live Logs) and verify they can execute using a valid API token in tests

## 3. Frontend & Streaming Integration

- [ ] 3.1 Implement SSE (Server-Sent Events) endpoint in FastAPI and verify it streams character-by-character output
- [ ] 3.2 Build the React Chat UI to consume the SSE stream and verify the UI updates smoothly without blocking
- [ ] 3.3 Add syntax highlighting and "Copy" buttons to the UI and verify that generated config files can be copied to the clipboard

## 4. Deployment & Infrastructure

- [ ] 4.1 Update the Dockerfile to support a multi-stage build (or split deployment) and verify the image builds locally
- [ ] 4.2 Update `liara.json` with disk definitions for the Vector DB and verify the configuration structure
- [ ] 4.3 Deploy the application to Liara and verify end-to-end functionality (chat, retrieval, code copying) in the production environment