# AI Tutor Project

This project aims to build a full-stack AI Tutor as a Chrome Extension using LangGraph, FastAPI, and various database technologies.

## Core Components

- **Framework**: LangGraph
- **Backend**: FastAPI
- **Databases**:
  - **ChromaDB**: Vector database for the knowledge base.
  - **PostgreSQL**: For the student model and long-term memory.
  - **Redis**: Session cache for short-term memory (e.g., authentication tokens, session context).
- **Frontend**: Chrome Extension

## Architecture

### The Master Coordinator (Delegator)

The central component of the system. It receives user requests and delegates them to the appropriate worker agent.

### Worker Agents

1.  **Navigator**: Navigates through course content to find specific modules.
2.  **Evaluator**: Assesses student answers, provides constructive feedback, and updates the student's profile in the PostgreSQL database.
3.  **Educate Agent**: Pulls information from the ChromaDB knowledge base and presents it in a clear, understandable way.
4.  **Math Agent**: A specialist for solving mathematical problems and explaining math concepts.
5.  **Study Plan Agent (Knowledge Gap Analysis)**: Acts as an academic advisor. It analyzes a student's progress from the PostgreSQL database to create personalized study schedules and learning paths.

### Memory and Knowledge Base

-   **Student Model (PostgreSQL)**: Long-term memory for student information and conversation history.
-   **Knowledge Base (ChromaDB)**: Contains COMP 237 material for fast, semantic information retrieval.
-   **Session Cache (Redis)**: Short-term memory for managing authentication tokens and session context.

### Feedback Loops

A dynamic process orchestrated by the Master Coordinator.

1.  **The Pedagogical Feedback Loop**:
    *   **Student**: Submits an answer.
    *   **Delegator**: Routes the answer to the **Evaluator Agent**.
    *   **Evaluator**: Assesses the response and updates the student's record in PostgreSQL.
    *   **Adaptation**: The system adapts the learning path based on the student's performance.

2.  **The Quality Feedback Loop**:
    *   **Functionality**: Thumbs up/down feature on agent responses.
    *   **Data Storage**: Feedback is stored in a PostgreSQL table.
    *   **Purpose**: To analyze agent performance and improve prompts over time.
