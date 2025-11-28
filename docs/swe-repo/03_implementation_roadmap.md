# Implementation Roadmap

## Phase 1: Data Injection & Validation (Immediate)
**Goal:** Make the agent "smart" about COMP 237.

- [ ] **Task 1.1:** Execute `scripts/ingest_course_data.py` targeting `raw_data/ExportFile_COMP237`.
- [ ] **Task 1.2:** Verify ChromaDB collection size and random retrieval quality.
- [ ] **Task 1.3:** Manually test "Law 1" (Scope) by asking out-of-scope questions (e.g., "How do I bake a cake?").

## Phase 2: Integration Testing (Week 1)
**Goal:** Ensure the frontend talks to the backend correctly under load.

- [ ] **Task 2.1:** Standardize Frontend Chat. Refactor `ChatContainer` to use `hooks/use-chat.ts`.
- [ ] **Task 2.2:** Test End-to-End Streaming. Verify markdown rendering and source citation display.
- [ ] **Task 2.3:** Test Admin Upload. Upload a new PDF via the extension and verify it appears in search.

## Phase 3: Code Execution & Mastery (Week 2)
**Goal:** Enable the "Tutor" capabilities.

- [ ] **Task 3.1:** Configure E2B Sandbox. Ensure `CodeExecutor` can run basic Python scripts.
- [ ] **Task 3.2:** Implement "Quiz Mode". When user asks for help, occasionally prompt a checking question.
- [ ] **Task 3.3:** Visualize Progress. Connect `student_mastery` table to the `ProgressChart` component.

## Phase 4: Polish & Deployment (Week 3)
**Goal:** Ship to students.

- [ ] **Task 4.1:** Build Production Extension (`npm run build`).
- [ ] **Task 4.2:** Deploy Backend to Render/Railway.
- [ ] **Task 4.3:** Distribute `.crx` file to beta testers (limited student group).

---

## Step-by-Step Execution Plan for "The Builder" (You)

1.  **Run the ETL script.** Don't write any code until the DB has data.
2.  **Fix the Frontend.** The dual chat implementation is a tech debt bomb. Pick one (`useChat.ts`) and stick to it.
3.  **Verify the Governor.** Ensure the "Cheating Detection" works. This is the core selling point to faculty.
4.  **Deploy.** Get it off localhost.


