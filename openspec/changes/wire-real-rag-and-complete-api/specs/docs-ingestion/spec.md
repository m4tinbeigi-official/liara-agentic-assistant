## Purpose

Provides an offline-capable pipeline that synchronizes the official Liara documentation repository, transforms Markdown/MDX into clean section-aware chunks, and indexes them with rich metadata for retrieval.

## ADDED Requirements

### Requirement: Source Synchronization
The system SHALL obtain documentation content from the official `liara-cloud/docs` GitHub repository and SHALL support idempotent re-ingestion without duplicating indexed points.

#### Scenario: Fresh ingest on empty collection
- **WHEN** ingestion runs against an empty or missing Qdrant collection
- **THEN** all cleaned chunks are indexed exactly once and point count equals chunk count

#### Scenario: Re-running ingestion
- **WHEN** ingestion runs a second time on an already-populated collection
- **THEN** the collection is replaced atomically and contains no duplicate chunk IDs

### Requirement: Structure-Aware Chunking
The system SHALL split documents at Markdown heading boundaries (H2/H3) with a maximum chunk size and bounded overlap.

#### Scenario: Document with frontmatter
- **WHEN** an MDX file contains YAML frontmatter or embedded component syntax
- **THEN** non-prose artifacts are stripped before chunking and no chunk exceeds the configured size limit

#### Scenario: Long section exceeding limit
- **WHEN** a single section exceeds the maximum chunk size
- **THEN** it is subdivided at paragraph boundaries while retaining the parent section title in payload metadata

### Requirement: Retrieval Metadata
Each indexed chunk SHALL carry `{url, section, platform, text}` so that any retrieved result can deep-link to the exact documentation section.

#### Scenario: Chunk payload completeness
- **WHEN** any point is stored in the collection
- **THEN** its payload includes a resolvable source URL and non-empty section title

### Requirement: Offline Startup Safety
The server SHALL start successfully when the collection is empty and MUST NOT block request handling to fetch remote sources.

#### Scenario: Server boot without internet
- **WHEN** the backend starts with an unreachable GitHub host and a populated local collection
- **THEN** startup completes and search serves from the existing index; a warning is logged only if the collection is also empty
