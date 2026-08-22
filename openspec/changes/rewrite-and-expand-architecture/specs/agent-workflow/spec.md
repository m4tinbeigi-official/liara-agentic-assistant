## Purpose

Provides a core decision-making and routing engine for the application using an Agent framework like ReAct or LangGraph.

## ADDED Requirements

### Requirement: Agent Intent Classification
The system SHALL classify incoming user requests to determine the appropriate tool or action to invoke.

#### Scenario: User provides an error log
- **WHEN** the input contains technical error traces or common error keywords
- **THEN** the system routes the request to the Diagnostic Agent

#### Scenario: User asks a general question about Liara
- **WHEN** the input is a general query regarding deployment or features
- **THEN** the system routes the request to the Docs RAG Agent

### Requirement: Tool Execution and Composition
The system SHALL execute necessary tools and synthesize their output into a unified response.

#### Scenario: Generating a configuration file
- **WHEN** the user requests a configuration for a specific framework
- **THEN** the system executes the Config Builder tool and presents the configuration alongside usage instructions