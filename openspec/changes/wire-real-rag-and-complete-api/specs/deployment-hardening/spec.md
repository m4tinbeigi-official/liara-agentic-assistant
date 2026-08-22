## Purpose

Hardens the production deployment for Liara PaaS: slim image (drop torch via ONNX embeddings), container health semantics, non-root runtime, and SSE resilience behind load balancers.

## ADDED Requirements

### Requirement: Slim Runtime Image
The production image SHALL avoid PyTorch by using an ONNX-based embedding runtime, and final image size SHALL be recorded in change notes.

#### Scenario: Image build
- **WHEN** `docker build` completes from a clean checkout including `frontend/package-lock.json`
- **THEN** all stages succeed and the reported final image size is documented

### Requirement: Container Health & Safety
The image SHALL define a HEALTHCHECK against `/health`, run as a non-root user, and expose only the Liara-assigned port.

#### Scenario: Healthy start
- **WHEN** the container starts with default environment
- **THEN** Docker reports healthy within 60 seconds and no process runs as UID 0

### Requirement: SSE Keep-Alive
The agent stream SHALL emit SSE comment pings during long tool executions so intermediate proxies do not close idle connections.

#### Scenario: Slow retrieval behind proxy
- **WHEN** a tool takes >15s before first content event and the stream traverses an nginx-class proxy
- **THEN** the connection remains open and the client eventually receives content and done events

### Requirement: Repository Integrity
Configuration files SHALL not reference non-existent scripts; local quick-start instructions SHALL be executable verbatim.

#### Scenario: Config reference audit
- **WHEN** every command/args entry in `mcp.json` and every shell snippet in `README.md` is resolved against the repo tree
- **THEN** each referenced path exists or the entry is removed
