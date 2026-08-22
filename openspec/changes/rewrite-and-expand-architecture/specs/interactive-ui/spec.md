## Purpose

Delivers a rich, modern, and interactive user interface tailored to streaming responses and displaying code snippets.

## ADDED Requirements

### Requirement: Streamed Agent Responses
The UI SHALL display the agent's thinking process and final answers progressively as they are generated.

#### Scenario: Long response generation
- **WHEN** the agent is generating a detailed troubleshooting guide
- **THEN** the UI updates character by character (streaming) without blocking the user

### Requirement: Actionable Code Snippets
The UI SHALL render code blocks with syntax highlighting and one-click actions.

#### Scenario: Displaying a generated liara.json
- **WHEN** a configuration file is presented
- **THEN** the UI provides a "Copy" button to instantly copy the contents to the clipboard