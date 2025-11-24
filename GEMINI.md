# Luminate AI Project Context

## Overview

Luminate AI is an agentic AI tutoring platform designed for Centennial College COMP 237.
The system includes a browser extension for student interaction and a backend for AI processing and data management.

## Project Structure

- **backend/**: Python-based backend services.
  - `main.py`: Entry point.
  - `app/`: Application logic.
  - `scripts/`: Utility scripts (e.g., video transcription).
- **extension/**: Browser extension built with Plasmo.
  - `src/`: Source code.
  - `assets/`: Static assets.
- **features/**: Feature-based organization.
  - `01-foundation/`, `02-auth/`, etc.
- **docs/**: Documentation files.
- **frontend_inspo/**: Frontend inspiration and components.

## Tech Stack

- **Extension**: Plasmo, React, TypeScript, Tailwind CSS, Shadcn UI.
- **Backend**: Python, FastAPI (assumed based on structure), LangChain.
- **AI Models**: Google Gemini 1.5 Pro/Flash, Vercel AI SDK.
- **Database**: Supabase.

## Development Guidelines

- Follow the feature-based directory structure in `features/`.
- Use `pnpm` for package management in the extension.
- Python dependencies are in `backend/requirements.txt`.


