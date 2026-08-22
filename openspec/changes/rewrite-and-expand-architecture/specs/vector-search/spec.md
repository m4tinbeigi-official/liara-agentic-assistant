## Purpose

Implements hybrid search capabilities (Dense Vector + BM25) over Liara's documentation to provide context for the RAG agent.

## ADDED Requirements

### Requirement: Document Embedding and Indexing
The system SHALL chunk and embed markdown/MDX files from the Liara docs repository into a persistent Vector Database.

#### Scenario: Indexing a new documentation release
- **WHEN** the indexing script is executed
- **THEN** the system parses the docs, creates embeddings, and stores them in the Vector DB on the persistent disk

### Requirement: Hybrid Search Execution
The system SHALL retrieve relevant context using a combination of semantic and keyword search.

#### Scenario: User searches for a specific CLI flag
- **WHEN** the user asks about `--api-token`
- **THEN** the system uses keyword search (BM25) to prioritize exact matches over semantic similarity