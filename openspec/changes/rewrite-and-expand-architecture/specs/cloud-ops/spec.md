## Purpose

Provides integration with the Liara Cloud API to perform operations like deploying and monitoring applications directly from the assistant.

## ADDED Requirements

### Requirement: User Authentication
The system SHALL allow users to authenticate using their Liara API token.

#### Scenario: Connecting API Token
- **WHEN** the user provides a valid Liara API token
- **THEN** the system validates the token and securely stores it for the session

### Requirement: Live Log Retrieval
The system SHALL fetch and display live logs from a user's running application on Liara.

#### Scenario: Fetching app logs
- **WHEN** the authenticated user requests logs for an app named `my-app`
- **THEN** the system streams the recent logs from the Liara API