# run_feedback_job.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.feedback_agent import FeedbackAgent

if __name__ == "__main__":
    agent = FeedbackAgent()
    result = agent.run_weekly_analysis(days=7)

    print("=== FeedbackAgent Weekly Analysis ===")
    print("Low-rated conversations analyzed:", result.get("num_bad_conversations"))
    print("Insights stored:", result.get("num_insights_stored"))
    print(result.get("message"))
