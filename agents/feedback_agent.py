"""
feedback_agent.py

FeedbackAgent – Internal QA / Critique Agent for the Luminate AI Tutoring System

This agent is NOT student-facing.

High-level responsibilities:
    1. Once per analysis cycle (e.g., weekly), scan PostgreSQL for
       low-rated conversations (1–2 stars).
    2. For each low-rated conversation, send the full interaction
       to a local LLM (Llama 3 via Ollama) in "critic" mode.
    3. The LLM analyzes:
         - Which agent was primarily responsible (PlannerAgent / TutorAgent / MathAgent)
         - What topic was being discussed
         - Root causes of failure (e.g., unclear explanation, routing error, wrong math)
         - Concrete suggestions for how that agent's strategy should change
    4. Store these insights into an analytics_insights table in PostgreSQL
       for HUMAN review – no automatic logic updates.

Intended schema (can be adjusted to match actual DB):

    chat_logs(
        conversation_id TEXT,
        turn_index      INT,
        role            TEXT,       -- 'student' or 'assistant'
        agent           TEXT,       -- 'PlannerAgent' | 'TutorAgent' | 'MathAgent' | NULL
        content         TEXT,
        created_at      TIMESTAMP
    )

    conversation_ratings(
        conversation_id TEXT,
        rating          INT,        -- 1–5 stars
        created_at      TIMESTAMP
    )

    analytics_insights(
        id                   SERIAL PRIMARY KEY,
        conversation_id      TEXT,
        topic                TEXT,
        primary_agent        TEXT,
        severity             TEXT,  -- 'low' | 'medium' | 'high'
        requires_human_review BOOLEAN,
        summary              TEXT,  -- human-readable summary of the issue
        raw_json             JSONB, -- full machine-readable insight object
        generated_at         TIMESTAMP DEFAULT NOW()
    )

You can schedule this agent weekly (or any interval) using:
    - a cron job calling `run_feedback_job.py`, or
    - an internal FastAPI endpoint that triggers run_weekly_analysis().
"""

from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import subprocess

import psycopg2
from psycopg2.extras import Json


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PG_DSN = "host=localhost dbname=ai_tutor user=postgres password=postgres"
LLM_MODEL = "llama3"  # name of the model in Ollama (e.g., "llama3", "llama3:8b")


# ---------------------------------------------------------------------
# Low-level LLM helper
# ---------------------------------------------------------------------

def call_llm(system_prompt: str, user_prompt: str, model: str = LLM_MODEL) -> str:
    """
    Call a local Ollama model (e.g., Llama 3) with a combined system + user prompt.

    Prompt structure:
        [SYSTEM]
        <system_prompt>

        [USER]
        <user_prompt>

    The model is expected to respond with plain text. In most cases,
    we will instruct it to output strict JSON for easier parsing.
    """
    full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}\n"

    result = subprocess.run(
        ["ollama", "run", model],
        input=full_prompt.encode("utf-8"),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------
# FeedbackAgent – internal QA / critique agent
# ---------------------------------------------------------------------

class FeedbackAgent:
    """
    Internal QA Agent for multi-agent tutoring system.

    This agent:
      - Retrieves low-rated conversations (rating <= 2) from PostgreSQL.
      - Sends them to the LLM as a "critic" to diagnose what went wrong.
      - Receives back structured JSON with topic, primary agent, root causes,
        and suggested strategy improvements.
      - Stores these insights in analytics_insights for HUMAN review.

    It does NOT automatically modify any strategies. It is a decision-support tool
    for the team and instructors.
    """

    def __init__(self, pg_dsn: str = PG_DSN, model: str = LLM_MODEL) -> None:
        self.pg_dsn = pg_dsn
        self.model = model

        # System prompt carefully designed for critique behavior
        self.system_prompt = (
            "You are an expert educational QA and AI-critique assistant for a "
            "multi-agent tutoring system.\n\n"
            "System overview:\n"
            "- PlannerAgent: classifies student messages and routes them to the right worker agent.\n"
            "- TutorAgent: explains conceptual and theoretical topics (e.g., AI, ML, algorithms) "
            "using a pedagogical, step-by-step style.\n"
            "- MathAgent: solves quantitative / math / coding problems and explains the steps.\n\n"
            "You receive FULL chat transcripts of conversations that students rated poorly "
            "(1 or 2 stars out of 5).\n"
            "Your job is NOT to re-answer the question, but to critique the system's behavior:\n"
            "- Identify which agent was primarily responsible for the poor experience.\n"
            "- Identify the topic or concept being discussed.\n"
            "- Diagnose the root causes of failure (e.g., incorrect math, missing steps, "
            "overly abstract explanation, planner misrouted the query, etc.).\n"
            "- Propose specific, concrete strategy changes that the corresponding agent "
            "should adopt (e.g., 'MathAgent must always show intermediate algebra steps', "
            "'TutorAgent should add a small real-world example when explaining backpropagation').\n\n"
            "You are writing for the developer / instructor team, not for students. "
            "Be honest, precise, and constructive. Do not be vague."
        )

    # -------------------------------------------------------------
    # DB Helper
    # -------------------------------------------------------------

    def _connect(self):
        """Return a new PostgreSQL connection."""
        return psycopg2.connect(self.pg_dsn)

    # -------------------------------------------------------------
    # Step 1: Fetch low-rated conversations
    # -------------------------------------------------------------

    def _fetch_low_rated_conversations(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch conversations with rating <= 2 in the last `days` days,
        and collect their full chat logs.

        Returns:
            List of dicts, each of the form:
            {
              "conversation_id": "...",
              "rating": 1 or 2,
              "messages": [
                {
                  "turn_index": int,
                  "role": "student" or "assistant",
                  "agent": "PlannerAgent" | "TutorAgent" | "MathAgent" | null,
                  "content": "message text",
                  "created_at": "ISO timestamp"
                },
                ...
              ]
            }
        """
        since = datetime.utcnow() - timedelta(days=days)
        bad_conversations: List[Dict[str, Any]] = []

        with self._connect() as conn:
            with conn.cursor() as cur:
                # Find conversations that received a rating <= 2 recently
                cur.execute(
                    """
                    SELECT conversation_id, rating
                    FROM conversation_ratings
                    WHERE created_at >= %s
                      AND rating <= 2
                    """,
                    (since,),
                )
                rated_rows = cur.fetchall()

            # For each low-rated conversation, fetch the full message log
            for conv_id, rating in rated_rows:
                with conn.cursor() as cur2:
                    cur2.execute(
                        """
                        SELECT turn_index, role, agent, content, created_at
                        FROM chat_logs
                        WHERE conversation_id = %s
                        ORDER BY turn_index ASC
                        """,
                        (conv_id,),
                    )
                    msg_rows = cur2.fetchall()

                messages = [
                    {
                        "turn_index": turn_idx,
                        "role": role,
                        "agent": agent,
                        "content": content,
                        "created_at": created_at.isoformat(),
                    }
                    for (turn_idx, role, agent, content, created_at) in msg_rows
                ]

                bad_conversations.append(
                    {
                        "conversation_id": conv_id,
                        "rating": rating,
                        "messages": messages,
                    }
                )

        return bad_conversations

    # -------------------------------------------------------------
    # Step 2: Build user prompt for critique
    # -------------------------------------------------------------

    def _build_user_prompt(self, bad_convos: List[Dict[str, Any]], days: int) -> str:
        """
        Build the user prompt given all low-rated conversations.
        We instruct the LLM to produce STRICT JSON per conversation.
        """
        conversations_json = json.dumps(bad_convos, indent=2)

        user_prompt = f"""
You are reviewing low-rated tutoring conversations from the LAST {days} DAYS.

Each item in the JSON below has:
  - conversation_id
  - rating (1 or 2 stars)
  - messages: ordered list of turns; each turn has:
      - turn_index: which turn in the conversation
      - role: "student" or "assistant"
      - agent: which internal agent responded ("PlannerAgent", "TutorAgent", "MathAgent", or null)
      - content: the actual text of the message
      - created_at: ISO timestamp

LOW-RATED CONVERSATIONS JSON:
{conversations_json}

For EACH conversation, you must produce a structured critique object with:

  - conversation_id: string
  - topic: a short topic label, e.g., "backpropagation", "A* search", "linear regression", or null if unclear
  - primary_agent: which agent seems MOST responsible for the poor outcome:
        "PlannerAgent" | "TutorAgent" | "MathAgent" | "mixed" | "unknown"
  - root_causes: a list of short strings (1–3 sentences each) describing the main reasons
        why the student likely gave a low rating. Be specific, e.g.,
        "TutorAgent explanation used too much jargon and skipped intuition."
  - suggested_changes: a list of short, concrete strategy changes that the developer team
        can implement for that agent. For example:
        - "TutorAgent should include at least one worked numerical example when explaining gradient descent."
        - "MathAgent must show intermediate algebra steps instead of jumping to the final answer."
        - "PlannerAgent should route 'explain' queries to TutorAgent instead of MathAgent."
  - severity: "low" | "medium" | "high"
        - high: serious misunderstanding, wrong math, or repeated failure
        - medium: explanation mostly correct but confusing or incomplete
        - low: minor style issue, answer mostly acceptable
  - requires_human_review: true or false
        (use true in most cases; set false only if the issue is extremely minor)

Return your output as STRICT JSON with the following top-level structure:

{{
  "insights": [
    {{
      "conversation_id": "...",
      "topic": "...",
      "primary_agent": "...",
      "root_causes": ["...", "..."],
      "suggested_changes": ["...", "..."],
      "severity": "low" | "medium" | "high",
      "requires_human_review": true
    }}
  ]
}}

Do NOT include any natural language outside of this JSON.
"""
        return user_prompt

    # -------------------------------------------------------------
    # Step 3: Store insights
    # -------------------------------------------------------------

    def _store_insights(self, insights: List[Dict[str, Any]]) -> None:
        """
        Insert each insight into analytics_insights.

        Each insight dict is expected to contain:
            - conversation_id
            - topic
            - primary_agent
            - severity
            - requires_human_review
            - root_causes
            - suggested_changes
        """
        if not insights:
            return

        with self._connect() as conn:
            with conn.cursor() as cur:
                for ins in insights:
                    summary_lines = []

                    # Build a human-readable summary string
                    topic = ins.get("topic") or "Unknown topic"
                    agent = ins.get("primary_agent") or "Unknown agent"
                    severity = ins.get("severity") or "unknown"

                    summary_lines.append(f"Topic: {topic}")
                    summary_lines.append(f"Primary agent: {agent}")
                    summary_lines.append(f"Severity: {severity}")

                    root_causes = ins.get("root_causes") or []
                    if root_causes:
                        summary_lines.append("Root causes:")
                        for rc in root_causes:
                            summary_lines.append(f"  - {rc}")

                    suggested_changes = ins.get("suggested_changes") or []
                    if suggested_changes:
                        summary_lines.append("Suggested changes:")
                        for sc in suggested_changes:
                            summary_lines.append(f"  - {sc}")

                    summary_text = "\n".join(summary_lines)

                    cur.execute(
                        """
                        INSERT INTO analytics_insights
                          (conversation_id,
                           topic,
                           primary_agent,
                           severity,
                           requires_human_review,
                           summary,
                           raw_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            ins.get("conversation_id"),
                            ins.get("topic"),
                            ins.get("primary_agent"),
                            ins.get("severity"),
                            bool(ins.get("requires_human_review", True)),
                            summary_text,
                            Json(ins),
                        ),
                    )

    # -------------------------------------------------------------
    # Public entrypoint – run weekly (or any interval) analysis
    # -------------------------------------------------------------

    def run_weekly_analysis(self, days: int = 7) -> Dict[str, Any]:
        """
        Main entrypoint.

        Typical usage from a cron job or admin endpoint:

            from feedback_agent import FeedbackAgent

            agent = FeedbackAgent()
            result = agent.run_weekly_analysis(days=7)
            print(result["summary"])

        Steps:
          1. Fetch all conversations rated <= 2 stars in the last `days`.
          2. If none, store a neutral insight and return.
          3. Build a critique prompt with all those conversations.
          4. Ask Llama (via Ollama) to analyze patterns and failure modes.
          5. Parse the returned JSON and store each insight in analytics_insights.
        """
        bad_convos = self._fetch_low_rated_conversations(days=days)

        if not bad_convos:
            neutral_summary = (
                f"No low-rated (1–2 star) conversations found in the last {days} days. "
                "No immediate QA action required."
            )
            # Store a neutral insight entry (optional but useful for history)
            self._store_insights(
                [
                    {
                        "conversation_id": None,
                        "topic": None,
                        "primary_agent": None,
                        "root_causes": [],
                        "suggested_changes": [],
                        "severity": "low",
                        "requires_human_review": False,
                    }
                ]
            )
            return {
                "num_bad_conversations": 0,
                "message": neutral_summary,
            }

        # Build the user prompt with all bad conversations
        user_prompt = self._build_user_prompt(bad_convos, days=days)

        # Call LLM
        raw_response = call_llm(self.system_prompt, user_prompt, model=self.model)

        # Try to parse JSON; if it fails, store a generic single insight with raw text
        try:
            data = json.loads(raw_response)
            insights = data.get("insights", [])
        except json.JSONDecodeError:
            # Fallback: wrap raw text as one generic insight
            insights = [
                {
                    "conversation_id": None,
                    "topic": None,
                    "primary_agent": "unknown",
                    "root_causes": [
                        "LLM returned non-JSON response during critique. "
                        "Developers should inspect raw_response."
                    ],
                    "suggested_changes": [],
                    "severity": "medium",
                    "requires_human_review": True,
                    "raw_response_text": raw_response,
                }
            ]

        # Store insights in DB
        self._store_insights(insights)

        return {
            "num_bad_conversations": len(bad_convos),
            "num_insights_stored": len(insights),
            "message": "FeedbackAgent analysis completed and stored in analytics_insights.",
        }


# Optional: allow running directly as a script for cron usage
if __name__ == "__main__":
    agent = FeedbackAgent()
    result = agent.run_weekly_analysis(days=7)
    print("=== FeedbackAgent Weekly Analysis ===")
    print("Low-rated conversations analyzed:", result["num_bad_conversations"])
    print("Insights stored:", result["num_insights_stored"])
    print(result["message"])
