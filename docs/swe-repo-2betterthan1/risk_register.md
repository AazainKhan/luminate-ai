# Risk Register
**Audience:** Humans & agents tracking delivery risk  
**Scope:** Current pilot; providers limited to Gemini/Groq.

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Vector store empty or stale | Agent gives generic answers | Run ETL (`scripts/ingest_course_data.py`) after any content change; verify with `verify_rag.py` and collection count | Open |
| Dual chat implementations drift | UX bugs / mismatch with backend | Keep `use-chat.ts` as the single path; remove/deprecate `lib/api.ts` streaming; manual SSE tests each PR | Open |
| Provider 404 / model mismatch | Broken chat | Use explicit IDs: `gemini-2.0-flash`, `gemini-1.5-pro-001`, Groq model names; document in env; add runtime validation | Open |
| Integrity/scope bypass | Faculty trust loss | Keep Governor logging enabled; add regression tests for policy denials; monitor denial events | Open |
| No automated tests | Regression risk | Add minimal backend chat/ETL smoke tests + frontend SSE test; gate merges on them | Open |
| Supabase auth drift | Users locked out | Keep `.env` in sync with Supabase project; add 401 handling in extension; periodic token sanity checks | Open |

**Owner placeholders:** Assign Engineer for ETL + chat, PM for GTM assets, QA for policy regression. Update owners in GitHub Issues.***
