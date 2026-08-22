## 1. Docs Ingestion Pipeline

- [ ] 1.1 Create `backend/ingestion.py` with git-clone/pull of `liara-cloud/docs` and MDX frontmatter stripping; verify on a 10-file sample that chunks preserve section titles
- [ ] 1.2 Implement section-aware Markdown chunking (H2/H3 boundaries, max ~800 tokens, 15% overlap) and verify no chunk exceeds the limit on the sample set
- [ ] 1.3 Index chunks into Qdrant with payload `{url, section, platform, text}` using fastembed embeddings; verify collection point count matches chunk count
- [ ] 1.4 Make ingestion idempotent (re-run replaces collection atomically); verify a second run does not duplicate points

## 2. Hybrid Retrieval

- [ ] 2.1 Add BM25 index (rank_bm25) built from the same chunk corpus at startup when `RAG_ENABLED=1`; verify keyword queries like `liara deploy --port` rank the correct doc first
- [ ] 2.2 Implement RRF fusion (k=60) merging Dense Top-20 + BM25 Top-20; verify golden-query Recall@3 >= 0.8 on a checked-in fixture of ~20 query/expected-doc pairs
- [ ] 2.3 Refactor `search_docs` to return structured results (`text`, `url`, `section`, `platform`, `score`) and update `agent.py` synthesis to append a "منابع" citation list; verify existing fallback still triggers only on zero valid hits
- [ ] 2.4 Gate new path behind `RAG_ENABLED` env flag; verify `RAG_ENABLED=0` reproduces current behavior exactly (existing e2e suite stays green)

## 3. API Surface Completion

- [ ] 3.1 Implement `POST /api/v1/agent/generate-config` with Pydantic body `{platform, app_name?, port?}` returning JSON config + instructions; add contract test
- [ ] 3.2 Implement `POST /api/v1/agent/diagnose` accepting `{log}` and reusing the diagnostic routing path; add contract test asserting remediation content for EADDRINUSE input
- [ ] 3.3 Implement `GET /api/v1/docs/search?q=&platform=` proxying hybrid retrieval; add contract tests for hit, filtered miss, and empty-query 422
- [ ] 3.4 Unify error envelope `{"error": {"code", "message_fa"}}` across all endpoints; verify chat endpoint keeps legacy shape for backward compatibility

## 4. Deployment Hardening

- [ ] 4.1 Replace sentence-transformers with fastembed in requirements and code; measure image size reduction and record before/after in this change's README
- [ ] 4.2 Add Docker HEALTHCHECK hitting `/health`, switch to non-root user, and pin Python base image digest; verify container starts and reports healthy locally
- [ ] 4.3 Add SSE keep-alive comment ping every 15s in `run_agent_stream`; verify an idle stream through a buffering proxy (nginx) is not closed for >=60s
- [ ] 4.4 Fix `mcp.json` entries pointing to non-existent files (remove or implement stub servers) and fix README local-start instructions (`npm start` → actual command sequence)

## 5. Verification & Docs

- [ ] 5.1 Full e2e suite green (9/9 existing + new contract tests)
- [ ] 5.2 Update `README.md` capability list to reflect real vs. planned features; remove overstatement where RAG was claimed but inactive
- [ ] 5.3 Record Recall@3 evaluation output in change notes; archive change after review
