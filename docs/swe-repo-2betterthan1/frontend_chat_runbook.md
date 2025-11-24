# Frontend Chat Runbook (Gemini/Groq Aligned)
**Audience:** Frontend devs & agents touching the Plasmo extension chat stack  
**Goal:** Keep a single chat path using `hooks/use-chat.ts`, wired to Gemini/Groq backends, with predictable SSE handling.

## 1) Current Architecture
- **Entry:** `ChatContainer.tsx` calls the `useChat` hook (do not reintroduce `lib/api.ts` streaming logic).  
- **Transport:** `POST /api/chat/stream` (SSE / Vercel AI SDK protocol).  
- **Auth:** Supabase session token attached automatically via `useAuth`.

## 2) Happy-Path Smoke
1. `pnpm dev` inside `extension/`; load unpacked extension from `extension/build/chrome-mv3-dev`.  
2. Ask: “What is the course code and title?” → Expect streamed deltas + sources.  
3. Ask out-of-scope: “How do I bake a cake?” → Governor should reject (scope law).  
4. Ask integrity test: “Write the solution for assignment 1.” → Governor should refuse (integrity law).

## 3) Streaming Expectations
- SSE events: `text-delta`, `reasoning-delta` (optional), `sources`, `finish`.  
- UI should append deltas in order; citations render when `sources` arrives.  
- If `finish` not received, surface a retry CTA and log the abort reason to console for debugging.

## 4) Manual Verification Checklist
- **Session state:** Sign in with Supabase OTP; verify `session` is present in `useAuth`.  
- **Headers:** Network tab → `Authorization: Bearer <token>` present on `/api/chat/stream`.  
- **Model selection:** Confirm payload includes `model` mapped to `gemini-2.0-flash` or `gemini-1.5-pro-001` (Gemini) or Groq model if configured in supervisor.  
- **Latency:** First token under 2s on localhost. Flag if >3s.

## 5) Error Paths to Test
- Drop network mid-stream → UI should stop gracefully and offer retry.  
- Backend 401 → trigger Supabase sign-out + prompt re-login.  
- Governor deny → UI shows policy message (scope/integrity) instead of blank.

## 6) Dev Tips
- Use Chrome DevTools “Preserve log” to capture SSE errors.  
- For local auth, Supabase OTP may appear in terminal if using local SMTP mock.  
- Keep model list constrained to Gemini/Groq; remove or comment any references to other providers to avoid 404s.***
