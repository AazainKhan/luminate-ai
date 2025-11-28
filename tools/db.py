# config/db.py
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from pathlib import Path

PG_OPTS = dict(
    host="localhost",
    port=5432,
    user="reet",
    password="",  # Empty password if you didn't set one
    dbname="ai_tutor",
)

@contextmanager
def _conn():
    print("Attempting to connect with PG_OPTS:", PG_OPTS)  # Add this line
    conn = psycopg2.connect(**PG_OPTS)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        print("Database error:", str(e))  # Add this line
        conn.rollback()
        raise
    finally:
        conn.close()

def init_schema_if_needed():
    # optional safety: re-run schema if you like
    sql_path = Path("data/sql/feedback_schema.sql")
    if not sql_path.exists():
        return
    with _conn() as c, c.cursor() as cur:
        cur.execute(sql_path.read_text(encoding="utf-8"))

def log_message(conversation_id: str, turn_index: int, role: str, content: str, agent: str | None = None):
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chat_logs (conversation_id, turn_index, role, agent, content)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (conversation_id, turn_index, role, agent, content),
        )

def save_rating(conversation_id: str, rating: int):
    rating = max(1, min(5, int(rating)))
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO conversation_ratings (conversation_id, rating)
            VALUES (%s, %s)
            ON CONFLICT (conversation_id) DO UPDATE SET rating = EXCLUDED.rating
            """,
            (conversation_id, rating),
        )

def get_conversation_history(conversation_id: str, limit: int = 10):
    """
    Retrieve recent conversation history for a given conversation_id.
    Returns list of messages in chronological order.
    """
    try:
        with _conn() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT turn_index, role, agent, content
                FROM chat_logs
                WHERE conversation_id = %s
                ORDER BY turn_index DESC
                LIMIT %s
                """,
                (conversation_id, limit),
            )
            rows = cur.fetchall()
            # Reverse to get chronological order (oldest first)
            return [dict(row) for row in reversed(rows)]
    except Exception as e:
        print(f"[WARNING] Could not retrieve conversation history: {e}")
        return []

def save_insight(conversation_id: str, topic: str, primary_agent: str, severity: str, summary: str, raw_json: str = "{}"):
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO analytics_insights (conversation_id, topic, primary_agent, severity, summary, raw_json)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (conversation_id, topic, primary_agent, severity, summary, raw_json),
        )
