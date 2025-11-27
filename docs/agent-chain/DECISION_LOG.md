# Decision Log (ADR)

Architecture Decision Records for significant technical decisions.

---

## ADR-001: WebdriverIO for E2E Testing

**Date:** 2025-01-13
**Status:** Accepted
**Context:** Need E2E testing for Chrome extension

**Decision:** Use WebdriverIO instead of Playwright

**Reasoning:**
- WebdriverIO has first-class Chrome extension support
- Better suited for side panel testing
- Plasmo examples use WebdriverIO patterns

**Consequences:**
- Need to build extension before tests
- Tests run in real Chrome browser
- CI requires Chrome installation

---

## ADR-002: Agent Chain Documentation System

**Date:** 2025-01-13
**Status:** Accepted
**Context:** Multiple AI agents work on this project across sessions

**Decision:** Create `docs/agent-chain/` with structured handover docs

**Reasoning:**
- Agents need shared context
- Prevents re-discovering project state
- Enables continuous improvement

**Consequences:**
- Agents must update CURRENT_STATUS.md before ending session
- Creates documentation overhead
- Requires discipline to maintain

---

## ADR-003: Conventional Commits Format

**Date:** 2025-01-13
**Status:** Accepted
**Context:** Standardize commit messages

**Decision:** Use `<type>(<scope>): <description>` format

**Reasoning:**
- Clear categorization of changes
- Enables automated changelog generation
- Industry standard practice

**Consequences:**
- All agents must follow format
- Makes git log more readable
- Scope helps track component changes

---

## Template

```markdown
## ADR-XXX: Title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Context:** Why is this decision needed?

**Decision:** What was decided?

**Reasoning:**
- Point 1
- Point 2

**Consequences:**
- Positive/negative outcome 1
- Positive/negative outcome 2
```
