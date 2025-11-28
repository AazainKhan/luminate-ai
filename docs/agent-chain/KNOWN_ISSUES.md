# Known Issues & Technical Debt

Track bugs, limitations, and tech debt for future resolution.

---

## 🔴 Critical

_None currently_

---

## 🟡 Medium Priority

### Issue: CI/CD Workflow Still Uses WebdriverIO
**Area:** Infra
**Description:** `.github/workflows/e2e-tests.yml` still references WebdriverIO commands
**Workaround:** E2E tests run locally with Playwright
**TODO:** Update workflow to use `npm run test:e2e` (Playwright)

---

## 🟢 Low Priority / Tech Debt

### Debt: No Unit Test Coverage for Agents
**Area:** Backend
**Description:** Agent nodes lack formal unit tests
**Impact:** Relies on manual testing
**TODO:** Add pytest tests for each agent node

### Debt: E2B Code Execution Quota
**Area:** Backend
**Description:** E2B free tier has limited executions
**Impact:** May fail if quota exceeded
**TODO:** Add fallback or quota monitoring

### Debt: Langfuse Observability Optional
**Area:** Backend
**Description:** Langfuse tracing disabled by default
**Impact:** No production observability
**TODO:** Enable for production deployment

### Debt: langchain-chroma Deprecation Warning
**Area:** Backend
**Description:** `Chroma` class from `langchain_community.vectorstores` is deprecated
**Workaround:** Still works, just logs warning
**TODO:** Run `pip install -U langchain-chroma` and update imports

---

## ✅ Resolved Issues

### ~~Issue: ChromaDB Using Docker Internal Hostname~~
**Resolved:** 2025-11-27
**Solution:** Changed `CHROMADB_HOST` from `memory_store` to `localhost` in backend/.env

### ~~Issue: WebdriverIO Deprecated CDP API~~
**Resolved:** 2025-11-27
**Solution:** Migrated to Playwright with `launchPersistentContext`

### ~~Issue: E2E Tests Need Mock Refinement~~
**Resolved:** 2025-11-27
**Solution:** Added dev auth bypass via `PLASMO_PUBLIC_DEV_AUTH_BYPASS` env var

### ~~Issue: Large Git Diff~~
**Resolved:** 2025-11-27
**Solution:** Committed changes in focused commits, updated gitignore

---

## Adding New Issues

```markdown
### Issue: Brief Title
**Area:** Backend | Extension | Testing | Docs | Infra
**Description:** What's the problem?
**Workaround:** How to work around it?
**TODO:** What needs to be done to fix it?
```
