# Agent Chain Documentation System

This directory contains living documentation for AI agents working on this project. The goal is to maintain continuity between agent sessions.

## Quick Links

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [CURRENT_STATUS.md](./CURRENT_STATUS.md) | Live project status | **EVERY SESSION** |
| [COMPLETED_WORK.md](./COMPLETED_WORK.md) | Work history log | When understanding context |
| [DECISION_LOG.md](./DECISION_LOG.md) | Architecture decisions | Before major changes |
| [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) | Bugs & tech debt | When debugging |

## How This Works

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT SESSION START                       │
│                                                              │
│   1. git pull origin main                                   │
│   2. Read CURRENT_STATUS.md                                 │
│   3. Review recent git log                                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DO THE WORK                               │
│                                                              │
│   • Make changes                                            │
│   • Test thoroughly                                         │
│   • Document decisions in DECISION_LOG.md                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT SESSION END                         │
│                                                              │
│   1. Update CURRENT_STATUS.md                               │
│   2. Log work in COMPLETED_WORK.md                          │
│   3. git add -A && git commit && git push                   │
└─────────────────────────────────────────────────────────────┘
```

## Commit Message Format

```
<type>(<scope>): <description>

Types: feat, fix, docs, refactor, test, chore
Scopes: agent, extension, backend, rag, auth, e2e
```

Examples:
- `feat(agent): add math derivation mode`
- `fix(auth): handle expired JWT tokens`
- `docs(agent-chain): update current status`
