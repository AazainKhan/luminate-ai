# Appendix B: System Specification

## Luminate AI Course Marshal

---

## B.1 Use Case List

| UC ID | Use Case Name | Actors | Description |
|-------|--------------|--------|-------------|
| UC-01 | Authenticate Student | Student, Supabase | Student logs in using OTP via institutional email |
| UC-02 | Authenticate Admin | Admin, Supabase | Faculty logs in with admin privileges |
| UC-03 | Ask Course Question | Student, AI Agent | Student asks a question about COMP 237 content |
| UC-04 | Receive Scaffolded Response | Student, AI Agent | AI provides pedagogically appropriate response |
| UC-05 | Execute Code | Student, E2B Sandbox | Student runs code in secure sandbox |
| UC-06 | Upload Course Materials | Admin, ETL Pipeline | Faculty uploads Blackboard export for ingestion |
| UC-07 | View System Health | Admin, Dashboard | Faculty checks system status and metrics |
| UC-08 | Track Mastery Progress | Student, Mastery System | Student views concept mastery scores |

---

## B.2 Use Case Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     LUMINATE AI COURSE MARSHAL                              │
│                         USE CASE DIAGRAM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌─────────────────────────────────────────┐              │
│                    │         System Boundary                 │              │
│                    │                                         │              │
│   ┌────────┐       │  ┌─────────────────────────────────┐   │              │
│   │        │       │  │                                 │   │              │
│   │Student │───────┼─▶│  UC-01: Authenticate Student    │   │              │
│   │        │       │  │                                 │   │              │
│   │        │       │  └─────────────────────────────────┘   │              │
│   │        │       │                                         │              │
│   │        │       │  ┌─────────────────────────────────┐   │              │
│   │        │───────┼─▶│  UC-03: Ask Course Question     │◀──┼─── <<uses>>  │
│   │        │       │  │  (Involves AI Agent)            │   │      │       │
│   │        │       │  └─────────────────────────────────┘   │      │       │
│   │        │       │                 │                      │      │       │
│   │        │       │                 ▼ <<includes>>         │      │       │
│   │        │       │  ┌─────────────────────────────────┐   │      │       │
│   │        │       │  │  UC-04: Receive Scaffolded      │   │      │       │
│   │        │───────┼─▶│  Response                       │   │      ▼       │
│   │        │       │  │  (AI provides guided answer)    │   │  ┌───────┐   │
│   │        │       │  └─────────────────────────────────┘   │  │ChromaDB   │
│   │        │       │                                         │  │ (RAG)  │   │
│   │        │       │  ┌─────────────────────────────────┐   │  └───────┘   │
│   │        │───────┼─▶│  UC-05: Execute Code            │   │              │
│   │        │       │  │  (E2B Sandbox)                  │   │              │
│   │        │       │  └─────────────────────────────────┘   │              │
│   │        │       │                                         │              │
│   │        │       │  ┌─────────────────────────────────┐   │              │
│   │        │───────┼─▶│  UC-08: Track Mastery Progress  │   │              │
│   │        │       │  │                                 │   │              │
│   └────────┘       │  └─────────────────────────────────┘   │              │
│                    │                                         │              │
│   ┌────────┐       │  ┌─────────────────────────────────┐   │              │
│   │        │       │  │                                 │   │              │
│   │ Admin  │───────┼─▶│  UC-02: Authenticate Admin      │   │              │
│   │(Faculty)│      │  │                                 │   │              │
│   │        │       │  └─────────────────────────────────┘   │              │
│   │        │       │                                         │              │
│   │        │       │  ┌─────────────────────────────────┐   │              │
│   │        │───────┼─▶│  UC-06: Upload Course Materials │   │              │
│   │        │       │  │  (ETL Pipeline)                 │   │              │
│   │        │       │  └─────────────────────────────────┘   │              │
│   │        │       │                                         │              │
│   │        │       │  ┌─────────────────────────────────┐   │              │
│   │        │───────┼─▶│  UC-07: View System Health      │   │              │
│   │        │       │  │                                 │   │              │
│   └────────┘       │  └─────────────────────────────────┘   │              │
│                    │                                         │              │
│                    └─────────────────────────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## B.3 Detailed Use Case Descriptions (AI-Involved)

### UC-03: Ask Course Question

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-03 |
| **Use Case Name** | Ask Course Question |
| **Actor(s)** | Student (Primary), AI Agent (System) |
| **Description** | Student submits a question about COMP 237 course content through the chat interface, and the AI agent processes and responds |
| **Preconditions** | 1. Student is authenticated via UC-01<br>2. System is operational<br>3. ChromaDB has course content indexed |
| **Trigger** | Student types and submits a question in the chat input |
| **Basic Flow** | 1. Student enters question in chat input<br>2. System validates authentication token<br>3. **Governor** checks policies (Law 1, Law 2)<br>4. If approved, **Supervisor** classifies intent<br>5. Request routed to appropriate agent (Tutor/Math/Coder)<br>6. **RAG** retrieves relevant context from ChromaDB<br>7. Agent generates response with scaffolding<br>8. Response streamed to frontend<br>9. Sources displayed to student |
| **Alternative Flows** | **3a. Scope Violation (Law 1)**<br>3a.1. Governor detects out-of-scope query<br>3a.2. System returns policy explanation<br>3a.3. Use case ends<br><br>**3b. Integrity Violation (Law 2)**<br>3b.1. Governor detects solution request<br>3b.2. System returns integrity explanation<br>3b.3. Use case ends |
| **Exception Flows** | **E1. Network Error**<br>E1.1. System displays connection error<br>E1.2. Student can retry<br><br>**E2. Model Timeout**<br>E2.1. System displays timeout message<br>E2.2. Student can retry |
| **Postconditions** | 1. Response displayed in chat<br>2. Interaction logged for analytics<br>3. Mastery score potentially updated |
| **Business Rules** | BR-01: Responses must cite source documents<br>BR-02: No complete solutions for graded work<br>BR-03: All queries must be COMP 237 relevant |

---

### UC-04: Receive Scaffolded Response

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-04 |
| **Use Case Name** | Receive Scaffolded Response |
| **Actor(s)** | Student (Primary), AI Agent (System) |
| **Description** | After a question is processed, the AI agent provides a pedagogically appropriate response based on the detected intent and student context |
| **Preconditions** | 1. UC-03 completed successfully<br>2. Governor approved the query<br>3. Intent classification completed |
| **Trigger** | Supervisor routes query to specialized agent |
| **Basic Flow** | **Tutor Intent:**<br>1. Pedagogical Tutor agent activated<br>2. Confusion detection checks student state<br>3. Scaffolding level determined (hint/guided/explain)<br>4. Socratic question formulated if appropriate<br>5. Response generated with teaching scaffolds<br>6. Follow-up question included for engagement<br><br>**Math Intent:**<br>1. Math Agent activated<br>2. Problem structure analyzed<br>3. Step-by-step derivation generated<br>4. LaTeX formatting applied<br>5. Visual intuition provided first<br>6. Practice problem suggested<br><br>**Code Intent:**<br>1. Code Agent (Groq) activated<br>2. Code context analyzed<br>3. Solution skeleton generated (not full solution)<br>4. Explanation of approach included<br>5. Run button enabled for sandbox execution |
| **Alternative Flows** | **4a. Student Confusion Detected**<br>4a.1. Override to Tutor mode<br>4a.2. Lower scaffolding level to "hint"<br>4a.3. Simpler explanation provided |
| **Exception Flows** | **E1. RAG retrieval empty**<br>E1.1. System indicates topic may not be covered<br>E1.2. General explanation provided with caveat |
| **Postconditions** | 1. Appropriate response delivered<br>2. Response matches intent type<br>3. Scaffolding appropriate to student level |

---

### UC-05: Execute Code

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-05 |
| **Use Case Name** | Execute Code |
| **Actor(s)** | Student (Primary), E2B Sandbox (System) |
| **Description** | Student executes Python code in a secure sandbox environment to test their understanding |
| **Preconditions** | 1. Code block displayed in chat<br>2. Student authenticated<br>3. E2B service available |
| **Trigger** | Student clicks "Run" button on code block |
| **Basic Flow** | 1. Student clicks Run button<br>2. Code extracted from code block<br>3. Request sent to `/api/execute` endpoint<br>4. E2B sandbox created<br>5. Code executed in isolated environment<br>6. Output (stdout/stderr) captured<br>7. Sandbox terminated<br>8. Results displayed below code block |
| **Alternative Flows** | **5a. Code contains errors**<br>5a.1. Error message captured<br>5a.2. Error displayed to student<br>5a.3. Hints provided for common errors |
| **Exception Flows** | **E1. Execution timeout**<br>E1.1. Sandbox terminated after 30s<br>E1.2. Timeout message displayed<br><br>**E2. E2B service unavailable**<br>E2.1. Error message displayed<br>E2.2. Student advised to try later |
| **Postconditions** | 1. Execution results displayed<br>2. Sandbox resources released<br>3. Execution logged for analytics |
| **Business Rules** | BR-04: Maximum execution time 30 seconds<br>BR-05: No network access from sandbox<br>BR-06: No file system persistence |

---

### UC-06: Upload Course Materials

| Field | Description |
|-------|-------------|
| **Use Case ID** | UC-06 |
| **Use Case Name** | Upload Course Materials |
| **Actor(s)** | Admin (Faculty), ETL Pipeline (System) |
| **Description** | Faculty uploads Blackboard export package for processing into the vector store |
| **Preconditions** | 1. Admin authenticated via UC-02<br>2. Valid Blackboard export ZIP file<br>3. ChromaDB service available |
| **Trigger** | Admin uploads file via admin dashboard |
| **Basic Flow** | 1. Admin navigates to Upload Materials tab<br>2. Admin selects/drags ZIP file<br>3. File uploaded to backend<br>4. **ETL Stage 1**: Archive extracted<br>5. **ETL Stage 2**: imsmanifest.xml parsed<br>6. **ETL Stage 3**: Documents processed and chunked<br>7. **ETL Stage 4**: Embeddings generated<br>8. **ETL Stage 5**: Chunks inserted to ChromaDB<br>9. Success confirmation displayed<br>10. Document count updated |
| **Alternative Flows** | **4a. Invalid file format**<br>4a.1. Error message displayed<br>4a.2. Upload cancelled |
| **Exception Flows** | **E1. Embedding service unavailable**<br>E1.1. ETL paused<br>E1.2. Admin notified<br>E1.3. Retry option provided |
| **Postconditions** | 1. Documents indexed in ChromaDB<br>2. Course content available for RAG<br>3. ETL log recorded |

---

## B.4 Functional Requirements

| ID | Requirement | Priority | Use Case | Status |
|----|-------------|----------|----------|--------|
| FR-01 | System shall authenticate users via Supabase OTP | High | UC-01, UC-02 | ✅ Implemented |
| FR-02 | System shall validate email domain for role assignment | High | UC-01, UC-02 | ✅ Implemented |
| FR-03 | System shall enforce scope policy (COMP 237 only) | High | UC-03 | ✅ Implemented |
| FR-04 | System shall enforce integrity policy (no solutions) | High | UC-03 | ✅ Implemented |
| FR-05 | System shall classify query intent automatically | High | UC-03 | ✅ Implemented |
| FR-06 | System shall route to specialized agents by intent | High | UC-04 | ✅ Implemented |
| FR-07 | System shall retrieve relevant context via RAG | High | UC-04 | ✅ Implemented |
| FR-08 | System shall stream responses to frontend | High | UC-04 | ✅ Implemented |
| FR-09 | System shall cite sources in responses | Medium | UC-04 | ✅ Implemented |
| FR-10 | System shall execute Python code in E2B sandbox | Medium | UC-05 | ✅ Implemented |
| FR-11 | System shall display execution results | Medium | UC-05 | ✅ Implemented |
| FR-12 | System shall accept Blackboard ZIP uploads | Medium | UC-06 | ✅ Implemented |
| FR-13 | System shall parse imsmanifest.xml | Medium | UC-06 | ✅ Implemented |
| FR-14 | System shall process PDF/DOCX/HTML documents | Medium | UC-06 | ✅ Implemented |
| FR-15 | System shall generate and store embeddings | Medium | UC-06 | ✅ Implemented |
| FR-16 | System shall display system health metrics | Low | UC-07 | ✅ Implemented |
| FR-17 | System shall track student mastery scores | Low | UC-08 | ✅ Implemented |
| FR-18 | System shall provide Socratic scaffolding | Medium | UC-04 | ✅ Implemented |
| FR-19 | System shall detect student confusion signals | Medium | UC-04 | ✅ Implemented |
| FR-20 | System shall support step-by-step math derivations | Medium | UC-04 | ✅ Implemented |

---

## B.5 Non-Functional Requirements

| ID | Requirement | Category | Target | Measurement |
|----|-------------|----------|--------|-------------|
| NFR-01 | Response latency (simple queries) | Performance | < 2 seconds | P95 response time |
| NFR-02 | Response latency (RAG queries) | Performance | < 5 seconds | P95 response time |
| NFR-03 | Code execution time | Performance | < 15 seconds | P95 execution time |
| NFR-04 | Time to first token | Performance | < 1 second | P95 TTFT |
| NFR-05 | System availability | Reliability | 99.9% uptime | Monthly availability |
| NFR-06 | Concurrent users supported | Scalability | 50 users | Load test capacity |
| NFR-07 | ChromaDB document capacity | Scalability | 10,000 chunks | Storage capacity |
| NFR-08 | Authentication latency | Performance | < 2 seconds | OTP verification time |
| NFR-09 | Policy enforcement accuracy | Accuracy | 100% | Test pass rate |
| NFR-10 | Intent classification accuracy | Accuracy | > 90% | Cross-validation |
| NFR-11 | Response accuracy | Accuracy | > 95% | Manual review |
| NFR-12 | Source citation rate | Quality | 100% | Automated check |
| NFR-13 | JWT validation | Security | Required | All API endpoints |
| NFR-14 | RLS enforcement | Security | Required | Database policies |
| NFR-15 | Sandbox isolation | Security | Required | E2B configuration |
| NFR-16 | Data encryption in transit | Security | TLS 1.3 | HTTPS enforcement |
| NFR-17 | Browser compatibility | Usability | Chrome 100+ | Testing coverage |
| NFR-18 | Mobile responsiveness | Usability | Side panel adapts | Visual testing |
| NFR-19 | Error message clarity | Usability | User-friendly | UX review |
| NFR-20 | Accessibility | Usability | WCAG 2.1 AA | Audit compliance |

---

*This appendix provides the system specification including use cases and requirements. Appendix C contains the system design documentation.*
