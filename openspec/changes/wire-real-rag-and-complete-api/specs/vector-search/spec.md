## Purpose

Upgrades document retrieval from single-vector search to Hybrid Search (Dense + BM25 fused via RRF) with structured, citable results — fulfilling ADR-001 for real instead of nominally.

## MODIFIED Requirements

### Requirement: Hybrid Retrieval
The system SHALL combine dense vector results and sparse BM25 keyword results using Reciprocal Rank Fusion, and SHALL return structured objects (`text`, `url`, `section`, `platform`, `score`) instead of a raw concatenated string.

#### Scenario: Exact keyword query
- **WHEN** the query contains an exact token from the docs (e.g., `liara deploy --port`)
- **THEN** the chunk containing that literal token ranks within the fused Top-3 even if dense similarity is low

#### Scenario: Paraphrased semantic query
- **WHEN** the query is a Persian paraphrase with no lexical overlap (e.g., «چطور اپم رو آپلود کنم»)
- **THEN** the semantically relevant deployment doc ranks within the fused Top-3

### Requirement: Graceful Degradation
The system SHALL fall back to curated answers only when zero valid results are returned, preserving current fallback behavior.

#### Scenario: Empty collection behind flag
- **WHEN** `RAG_ENABLED=1` but the collection is empty or unavailable
- **THEN** retrieval returns an empty list, the agent uses its curated fallback, and no error surfaces to the user

#### Scenario: Legacy mode
- **WHEN** `RAG_ENABLED=0`
- **THEN** behavior is byte-compatible with the pre-change release and all existing e2e tests pass unchanged

### Requirement: Retrieval Quality Gate
Hybrid retrieval SHALL achieve Recall@3 >= 0.8 on a version-controlled golden query set before the capability is considered done.

#### Scenario: Golden set evaluation
- **WHEN** the evaluation script runs against the golden fixture (~20 query/expected-doc pairs)
- **THEN** reported Recall@3 meets the threshold and the output is recorded in change notes
