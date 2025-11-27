# Agent Instructions

> Quick start guide for AI agents working on this project.

## 🚦 Session Start Checklist

```bash
# 1. Get latest changes
git pull origin main

# 2. Read current status (MANDATORY)
cat docs/agent-chain/CURRENT_STATUS.md

# 3. Check recent activity
git log --oneline -10

# 4. Verify backend works
cd backend
source venv/bin/activate
python -c "from app.agents.tutor_agent import run_agent; print('✅ Agent OK')"
```

## 🏗️ Key Architecture

```
User Query → Governor (3 Laws) → Supervisor (Intent Routing) → Specialized Agent → Evaluator → Response
```

**Files to know:**
- `backend/app/agents/tutor_agent.py` - Entry point
- `backend/app/agents/state.py` - AgentState TypedDict
- `extension/src/sidepanel.tsx` - Main UI

## 📝 Making Changes

1. **Test locally first** - Always verify changes work
2. **Document decisions** - Update `docs/agent-chain/DECISION_LOG.md`
3. **Log issues** - Add to `KNOWN_ISSUES.md`

## 🎯 Commit Format

```
<type>(<scope>): <description>

Types: feat, fix, docs, refactor, test, chore
Scopes: agent, extension, backend, rag, auth, e2e
```

## 🏁 Session End Checklist

```bash
# 1. Stage and commit
git add -A
git commit -m "type(scope): description"

# 2. Update status doc
# Edit docs/agent-chain/CURRENT_STATUS.md

# 3. Log your work
# Add entry to docs/agent-chain/COMPLETED_WORK.md

# 4. Push
git push origin main
```

## 📚 Documentation Map

| Need | Look Here |
|------|-----------|
| Project overview | `README.md` |
| Live status | `docs/agent-chain/CURRENT_STATUS.md` |
| Full context | `docs/for-next-agent/HANDOVER.md` |
| Coding guidelines | `.github/copilot-instructions.md` |
| Feature specs | `features/` directory |
