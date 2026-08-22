## Purpose

Implements the three documented-but-missing endpoints from the project spec (`/agent/diagnose`, `/agent/generate-config`, `/docs/search`) with typed validation and a unified error envelope, closing the gap between `spec.md` §4 and the running service.

## ADDED Requirements

### Requirement: Diagnose Endpoint
`POST /api/v1/agent/diagnose` SHALL accept `{log: string}` and return a streaming SSE remediation plan identical in event format to the chat stream.

#### Scenario: Port binding error submitted
- **WHEN** a log containing `EADDRINUSE` is posted
- **THEN** the response streams tool events followed by a remediation plan that includes the `PORT` environment guidance

#### Scenario: Missing log field
- **WHEN** the body lacks a non-empty `log`
- **THEN** the API responds 422 with the unified error envelope

### Requirement: Generate Config Endpoint
`POST /api/v1/agent/generate-config` SHALL accept `{platform, app_name?, port?}` with validation against supported platforms and return the generated `liara.json` content as JSON.

#### Scenario: Supported platform
- **WHEN** `{platform: "django"}` is posted without optional fields
- **THEN** the response contains a valid config with resolved defaults (`app_name`, `port`) and usage instructions

#### Scenario: Unsupported platform
- **WHEN** `{platform: "cobol"}` is posted
- **THEN** the API responds 422 listing supported platforms in `message_fa`

### Requirement: Docs Search Endpoint
`GET /api/v1/docs/search` SHALL proxy hybrid retrieval with optional platform filtering.

#### Scenario: Query with results
- **WHEN** `?q=node&platform=nodejs` matches indexed docs
- **THEN** the response returns an array of structured results including `url` citations

#### Scenario: Empty query
- **WHEN** `q` is missing or blank
- **THEN** the API responds 422 with the unified error envelope

### Requirement: Unified Error Envelope
New endpoints SHALL return errors as `{"error": {"code", "message_fa"}}` with appropriate HTTP status (422 validation, 503 dependency failure); the existing chat endpoint SHALL retain its current shape for backward compatibility.

#### Scenario: Downstream dependency down
- **WHEN** retrieval dependencies are unavailable for `/docs/search`
- **THEN** the response is 503 with code `RETRIEVAL_UNAVAILABLE`, not a raw traceback
