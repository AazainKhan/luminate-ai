"""
Feedback Learning System for Orchestrator
Captures user corrections when they manually switch modes after auto-routing.

This helps the orchestrator learn from mistakes and improve over time.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

# Database path
FEEDBACK_DB_PATH = Path(__file__).parent.parent / "data" / "orchestrator_feedback.db"


class FeedbackStore:
    """SQLite-based storage for orchestrator feedback."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or FEEDBACK_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mode_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    predicted_mode TEXT NOT NULL,
                    actual_mode TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    student_id TEXT,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    conversation_context TEXT,
                    was_follow_up BOOLEAN DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON mode_feedback(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_predicted_actual 
                ON mode_feedback(predicted_mode, actual_mode)
            """)
            
            # Analytics table for aggregated metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weekly_analytics (
                    week_start TEXT PRIMARY KEY,
                    total_predictions INTEGER,
                    correct_predictions INTEGER,
                    accuracy REAL,
                    navigate_to_educate INTEGER,
                    educate_to_navigate INTEGER,
                    low_confidence_errors INTEGER,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def record_feedback(
        self, 
        query: str,
        predicted_mode: str,
        actual_mode: str,
        confidence: float,
        reasoning: str = "",
        student_id: str = "anonymous",
        session_id: str = "",
        conversation_context: Optional[List[Dict]] = None,
        was_follow_up: bool = False
    ):
        """
        Record when user manually switches modes after auto-routing.
        
        Args:
            query: The user's query
            predicted_mode: What the orchestrator selected
            actual_mode: What the user manually switched to
            confidence: Orchestrator's confidence (0-1)
            reasoning: Orchestrator's reasoning
            student_id: Student identifier
            session_id: Session identifier
            conversation_context: Recent conversation history
            was_follow_up: Whether this was detected as a follow-up
        """
        # Only record if prediction was wrong
        if predicted_mode == actual_mode:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO mode_feedback 
                (query, predicted_mode, actual_mode, confidence, reasoning, 
                 student_id, session_id, timestamp, conversation_context, was_follow_up)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query,
                predicted_mode,
                actual_mode,
                confidence,
                reasoning,
                student_id,
                session_id,
                datetime.now().isoformat(),
                json.dumps(conversation_context) if conversation_context else None,
                was_follow_up
            ))
            conn.commit()
        
        print(f"📊 Feedback recorded: {predicted_mode} → {actual_mode} (confidence={confidence:.2f})")
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent classification errors for analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM mode_feedback
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_low_confidence_errors(self, confidence_threshold: float = 0.7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get errors where confidence was low (useful for improving thresholds)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM mode_feedback
                WHERE confidence < ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (confidence_threshold, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_accuracy_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get accuracy statistics for recent period.
        Note: This requires tracking ALL predictions, not just errors.
        For now, returns error patterns.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_errors,
                    SUM(CASE WHEN predicted_mode = 'navigate' AND actual_mode = 'educate' THEN 1 ELSE 0 END) as nav_to_edu,
                    SUM(CASE WHEN predicted_mode = 'educate' AND actual_mode = 'navigate' THEN 1 ELSE 0 END) as edu_to_nav,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN was_follow_up = 1 THEN 1 ELSE 0 END) as follow_up_errors
                FROM mode_feedback
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
            """, (days,))
            
            row = cursor.fetchone()
            
            return {
                "total_errors": row[0],
                "navigate_to_educate_errors": row[1],
                "educate_to_navigate_errors": row[2],
                "avg_error_confidence": round(row[3], 3) if row[3] else 0,
                "follow_up_errors": row[4],
                "period_days": days
            }
    
    def generate_weekly_report(self) -> str:
        """Generate a human-readable weekly report."""
        stats = self.get_accuracy_stats(days=7)
        recent_errors = self.get_recent_errors(limit=10)
        low_conf_errors = self.get_low_confidence_errors(limit=5)
        
        report = f"""
🔍 Orchestrator Feedback Report (Last 7 Days)
{'=' * 60}

📊 Error Statistics:
  - Total errors: {stats['total_errors']}
  - Navigate → Educate errors: {stats['navigate_to_educate_errors']}
  - Educate → Navigate errors: {stats['educate_to_navigate_errors']}
  - Follow-up detection errors: {stats['follow_up_errors']}
  - Average error confidence: {stats['avg_error_confidence']:.2%}

⚠️  Recent Errors:
"""
        for i, error in enumerate(recent_errors[:5], 1):
            report += f"  {i}. \"{error['query'][:50]}...\"\n"
            report += f"     Predicted: {error['predicted_mode']}, Actual: {error['actual_mode']}\n"
            report += f"     Confidence: {error['confidence']:.2f}\n\n"
        
        if low_conf_errors:
            report += "\n🎯 Low Confidence Errors (< 0.7):\n"
            for i, error in enumerate(low_conf_errors, 1):
                report += f"  {i}. \"{error['query'][:50]}...\" (conf={error['confidence']:.2f})\n"
        
        report += "\n" + "=" * 60
        
        return report


# Global instance
feedback_store = FeedbackStore()


def record_mode_switch(
    query: str,
    predicted_mode: str,
    actual_mode: str,
    confidence: float,
    reasoning: str = "",
    student_id: str = "anonymous",
    session_id: str = "",
    conversation_context: Optional[List[Dict]] = None,
    was_follow_up: bool = False
):
    """
    Convenience function to record feedback.
    Call this from the frontend when user manually switches modes.
    """
    feedback_store.record_feedback(
        query=query,
        predicted_mode=predicted_mode,
        actual_mode=actual_mode,
        confidence=confidence,
        reasoning=reasoning,
        student_id=student_id,
        session_id=session_id,
        conversation_context=conversation_context,
        was_follow_up=was_follow_up
    )


def get_feedback_stats(days: int = 7) -> Dict[str, Any]:
    """Get feedback statistics."""
    return feedback_store.get_accuracy_stats(days=days)


def generate_report() -> str:
    """Generate weekly feedback report."""
    return feedback_store.generate_weekly_report()


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # Test the feedback system
    print("🧪 Testing Feedback System\n")
    
    # Simulate some feedback
    test_cases = [
        {
            "query": "explain how gradient descent works",
            "predicted": "navigate",
            "actual": "educate",
            "confidence": 0.65,
            "reasoning": "Low confidence prediction"
        },
        {
            "query": "find me videos about neural networks",
            "predicted": "educate",
            "actual": "navigate",
            "confidence": 0.72,
            "reasoning": "Misclassified due to neural networks keyword"
        },
        {
            "query": "what about backpropagation?",
            "predicted": "navigate",
            "actual": "educate",
            "confidence": 0.55,
            "reasoning": "Failed to detect follow-up context",
            "was_follow_up": True
        }
    ]
    
    for case in test_cases:
        record_mode_switch(
            query=case["query"],
            predicted_mode=case["predicted"],
            actual_mode=case["actual"],
            confidence=case["confidence"],
            reasoning=case["reasoning"],
            session_id="test-session",
            was_follow_up=case.get("was_follow_up", False)
        )
    
    # Generate report
    print(generate_report())
    
    # Show recent errors
    print("\n📋 Recent Errors Detail:")
    errors = feedback_store.get_recent_errors(limit=5)
    for error in errors:
        print(f"\nQuery: {error['query']}")
        print(f"Predicted: {error['predicted_mode']} → Actual: {error['actual_mode']}")
        print(f"Confidence: {error['confidence']}, Follow-up: {error['was_follow_up']}")


