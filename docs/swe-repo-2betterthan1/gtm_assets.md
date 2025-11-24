# GTM Assets Checklist
**Product:** Centennial Course Marshal  
**Audience:** Humans (product/ops/marketing)  
**Models:** Gemini/Groq only (no external provider references).

## Core Assets
- **Demo video (60s):** Show question → grounded answer with citation → integrity refusal → code execution (if enabled) → quick win. Capture latency and citation pop.  
- **One-pager (faculty-facing):** Safety (Governor laws), curriculum alignment (COMP 237), data residency (local Chroma), auth (institutional email via Supabase), models (Gemini/Groq).  
- **Install guide (students):** Side-load extension steps, OTP login, first chat, troubleshooting (OTP email, scope denials).

## Pilot Metrics to Capture
- Weekly active users (% of pilot cohort).  
- Median first-token latency.  
- Denial rates by Governor law (scope vs integrity).  
- Citation presence rate (answers with sources attached).  
- Top 10 question intents (to refine content gaps).

## Launch Sequencing
- **Beta (30 students + 1 prof):** Ship side-loaded CRX, monitor logs/latency, collect denials.  
- **Official (department):** Require institutional email enforcement, publish install guide via LMS, run FERPA-compliance review for stored data in Chroma/Postgres.

## Wild Ideas (Within Providers)
- Pre-cache embeddings for syllabus highlights to speed first-token.  
- Groq for long-form reasoning, Gemini Flash for fast responses; route by intent.  
- “Quiz mode” toggle that occasionally asks a mastery check before revealing answers.***
