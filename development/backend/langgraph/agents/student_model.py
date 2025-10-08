"""
Student Model Agent - Tracks and updates student understanding

Based on evidence-based ITS principles:
- Knowledge tracing (what student knows)
- Misconception detection
- Difficulty adaptation
- Spacing effect (when to review)
- Metacognitive awareness

This is the "intelligence" behind personalized tutoring.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class StudentModel:
    """
    Maintains student understanding model using Bayesian Knowledge Tracing principles.
    Tracks: mastery per topic, common misconceptions, optimal review timing
    """
    
    def __init__(self, student_context: Dict[str, Any] = None):
        """Initialize student model from context or create new"""
        if student_context is None:
            student_context = {}
        
        self.student_id = student_context.get('student_id', 'anonymous')
        self.mastery_map = student_context.get('mastery_map', {})  # topic -> mastery_level (0-1)
        self.misconceptions = student_context.get('misconceptions', {})  # topic -> [misconception_ids]
        self.interaction_history = student_context.get('interaction_history', [])
        self.struggling_topics = student_context.get('struggling_topics', [])
        self.review_schedule = student_context.get('review_schedule', {})  # topic -> next_review_date
        self.learning_pace = student_context.get('learning_pace', 'medium')  # slow, medium, fast
        
    def estimate_mastery(self, topic: str) -> float:
        """
        Estimate student's mastery of a topic (0.0 - 1.0)
        
        Uses evidence from:
        - Previous correct/incorrect answers
        - Time since last interaction
        - Related topic performance
        
        Returns:
            Mastery probability (0.0 = no knowledge, 1.0 = mastered)
        """
        if topic in self.mastery_map:
            base_mastery = self.mastery_map[topic]
            
            # Apply forgetting curve ONLY if we have interaction history
            # Otherwise mastery was just set without time passage
            topic_interactions = [i for i in self.interaction_history if i['topic'] == topic]
            if topic_interactions:
                # Apply forgetting curve (Ebbinghaus)
                days_since_last = self._days_since_last_interaction(topic)
                if days_since_last > 0:
                    # Forgetting: retention = base * e^(-days/strength)
                    strength = 7.0  # Days to retain 50% (configurable based on mastery)
                    retention_factor = 0.5 ** (days_since_last / strength)
                    adjusted_mastery = base_mastery * (0.5 + 0.5 * retention_factor)
                    return max(0.0, min(1.0, adjusted_mastery))
            
            return base_mastery
        else:
            # No data: check if related topics are mastered
            related_mastery = self._infer_from_related_topics(topic)
            return related_mastery if related_mastery is not None else 0.2  # Slight prior
    
    def update_mastery(self, topic: str, performance: Dict[str, Any]):
        """
        Update mastery estimate based on new evidence (Bayesian update)
        
        Args:
            topic: Topic being learned
            performance: {
                'correct': bool,
                'confidence': float (0-1),
                'time_taken': float (seconds),
                'hint_level_used': int (0=none, 1-3)
            }
        """
        current_mastery = self.estimate_mastery(topic)
        
        # Evidence strength based on performance
        if performance.get('correct'):
            # Correct answer increases mastery
            hint_penalty = 0.3 * performance.get('hint_level_used', 0) / 3.0
            confidence_boost = performance.get('confidence', 0.7)
            evidence_strength = confidence_boost - hint_penalty
            
            # Larger update if student was uncertain before
            update_magnitude = evidence_strength * (1 - current_mastery) * 0.4
            new_mastery = current_mastery + update_magnitude
        else:
            # Incorrect answer decreases mastery or reveals lack
            evidence_strength = 1.0 - performance.get('confidence', 0.3)
            update_magnitude = evidence_strength * current_mastery * 0.3
            new_mastery = current_mastery - update_magnitude
        
        self.mastery_map[topic] = max(0.0, min(1.0, new_mastery))
        
        # Update struggling topics list
        if new_mastery < 0.3 and topic not in self.struggling_topics:
            self.struggling_topics.append(topic)
        elif new_mastery > 0.6 and topic in self.struggling_topics:
            self.struggling_topics.remove(topic)
        
        # Schedule next review using spaced repetition
        self._schedule_review(topic, new_mastery)
        
        # Record interaction
        self.interaction_history.append({
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'mastery_before': current_mastery,
            'mastery_after': new_mastery,
            'performance': performance
        })
    
    def detect_misconception(self, topic: str, student_answer: str, correct_answer: str) -> Optional[str]:
        """
        Detect specific misconception from incorrect answer pattern
        
        Returns:
            Misconception ID if detected, None otherwise
        """
        # Common COMP237 misconceptions database
        misconception_patterns = {
            'dfs_bfs': {
                'pattern': r'dfs.*breadth|bfs.*depth',
                'id': 'search_algorithm_confusion',
                'explanation': 'Confusing DFS (depth-first) with BFS (breadth-first)'
            },
            'supervised_unsupervised': {
                'pattern': r'supervised.*no labels|unsupervised.*labels',
                'id': 'ml_paradigm_confusion',
                'explanation': 'Mixing up supervised (with labels) and unsupervised (no labels)'
            },
            'precision_recall': {
                'pattern': r'precision.*false negative|recall.*false positive',
                'id': 'metric_confusion',
                'explanation': 'Confusing precision (FP) and recall (FN) denominators'
            },
            'overfitting_underfitting': {
                'pattern': r'overfit.*too simple|underfit.*too complex',
                'id': 'fitting_confusion',
                'explanation': 'Reversing overfitting (too complex) and underfitting (too simple)'
            }
        }
        
        import re
        student_lower = student_answer.lower()
        
        for misconception_data in misconception_patterns.values():
            if re.search(misconception_data['pattern'], student_lower):
                misconception_id = misconception_data['id']
                
                # Track this misconception
                if topic not in self.misconceptions:
                    self.misconceptions[topic] = []
                if misconception_id not in self.misconceptions[topic]:
                    self.misconceptions[topic].append(misconception_id)
                
                return misconception_id
        
        return None
    
    def recommend_difficulty(self, topic: str) -> str:
        """
        Recommend question difficulty based on current mastery (ZPD principle)
        
        Returns:
            'easy', 'medium', 'hard', or 'challenge'
        """
        mastery = self.estimate_mastery(topic)
        
        # Zone of Proximal Development: slightly above current level
        if mastery < 0.3:
            return 'easy'  # Build foundation
        elif mastery < 0.6:
            return 'medium'  # Core practice
        elif mastery < 0.85:
            return 'hard'  # Deepen understanding
        else:
            return 'challenge'  # Push boundaries
    
    def should_review(self, topic: str) -> bool:
        """
        Check if topic needs review based on spaced repetition schedule
        
        Returns:
            True if review is due
        """
        if topic not in self.review_schedule:
            return False
        
        next_review = datetime.fromisoformat(self.review_schedule[topic])
        return datetime.now() >= next_review
    
    def get_prerequisite_gaps(self, topic: str, topic_graph: Dict[str, List[str]]) -> List[str]:
        """
        Identify prerequisite topics the student hasn't mastered
        
        Args:
            topic: Target topic
            topic_graph: {topic: [prerequisite_topics]}
        
        Returns:
            List of prerequisite topics with mastery < 0.5
        """
        prerequisites = topic_graph.get(topic, [])
        gaps = []
        
        for prereq in prerequisites:
            if self.estimate_mastery(prereq) < 0.5:
                gaps.append(prereq)
        
        return gaps
    
    def suggest_next_topics(self, topic_graph: Dict[str, List[str]], n: int = 3) -> List[Dict[str, Any]]:
        """
        Suggest next topics to study based on:
        - Mastered prerequisites
        - Current struggling areas
        - Spaced repetition schedule
        
        Returns:
            List of {topic, reason, priority}
        """
        suggestions = []
        
        # Priority 1: Review topics due for spaced repetition
        for topic, next_review in self.review_schedule.items():
            if self.should_review(topic):
                suggestions.append({
                    'topic': topic,
                    'reason': f'Review due (last studied {self._days_since_last_interaction(topic)} days ago)',
                    'priority': 1,
                    'type': 'review'
                })
        
        # Priority 2: Address struggling topics
        for topic in self.struggling_topics[:2]:
            suggestions.append({
                'topic': topic,
                'reason': f'Low mastery ({self.estimate_mastery(topic):.0%}) - needs practice',
                'priority': 2,
                'type': 'remediation'
            })
        
        # Priority 3: New topics with prerequisites met
        for topic in topic_graph.keys():
            if topic not in self.mastery_map:  # New topic
                prereqs = topic_graph.get(topic, [])
                prereq_mastery = [self.estimate_mastery(p) for p in prereqs] if prereqs else [1.0]
                
                if all(m >= 0.6 for m in prereq_mastery):
                    avg_prereq_mastery = sum(prereq_mastery) / len(prereq_mastery)
                    suggestions.append({
                        'topic': topic,
                        'reason': f'Prerequisites mastered ({avg_prereq_mastery:.0%})',
                        'priority': 3,
                        'type': 'new'
                    })
        
        # Sort by priority and return top N
        suggestions.sort(key=lambda x: (x['priority'], -self.estimate_mastery(x['topic'])))
        return suggestions[:n]
    
    def _days_since_last_interaction(self, topic: str) -> int:
        """Calculate days since last interaction with topic"""
        topic_interactions = [i for i in self.interaction_history if i['topic'] == topic]
        if not topic_interactions:
            return 999  # Very old or never
        
        last_interaction = max(topic_interactions, key=lambda x: x['timestamp'])
        last_time = datetime.fromisoformat(last_interaction['timestamp'])
        return (datetime.now() - last_time).days
    
    def _schedule_review(self, topic: str, mastery: float):
        """Schedule next review using spaced repetition algorithm (SM-2 variant)"""
        # Interval based on mastery level
        if mastery < 0.3:
            interval_days = 1  # Review tomorrow
        elif mastery < 0.6:
            interval_days = 3  # Review in 3 days
        elif mastery < 0.85:
            interval_days = 7  # Review in a week
        else:
            interval_days = 14  # Review in 2 weeks
        
        next_review = datetime.now() + timedelta(days=interval_days)
        self.review_schedule[topic] = next_review.isoformat()
    
    def _infer_from_related_topics(self, topic: str) -> Optional[float]:
        """Infer mastery from related topics (simple heuristic)"""
        # Could use topic embeddings or knowledge graph here
        # For now, return None to indicate no inference
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export student model for persistence"""
        return {
            'student_id': self.student_id,
            'mastery_map': self.mastery_map,
            'misconceptions': self.misconceptions,
            'interaction_history': self.interaction_history[-50:],  # Keep last 50
            'struggling_topics': self.struggling_topics,
            'review_schedule': self.review_schedule,
            'learning_pace': self.learning_pace,
            'updated_at': datetime.now().isoformat()
        }


def student_model_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update student model based on current interaction
    
    Args:
        state: Contains 'query', 'student_context', optional 'student_response'
        
    Returns:
        Updated state with enhanced student_context and recommendations
    """
    # Load or create student model
    student_context = state.get('student_context', {})
    model = StudentModel(student_context)
    
    # Extract topic from query
    query = state.get('query', '').lower()
    topic = _extract_topic_from_query(query)
    
    # Get current mastery
    mastery = model.estimate_mastery(topic)
    
    # If student provided an answer (quiz/practice), update mastery
    if 'student_response' in state:
        response = state['student_response']
        performance = {
            'correct': response.get('correct', False),
            'confidence': response.get('confidence', 0.5),
            'time_taken': response.get('time_taken', 0),
            'hint_level_used': response.get('hint_level_used', 0)
        }
        model.update_mastery(topic, performance)
        
        # Detect misconceptions if incorrect
        if not performance['correct']:
            misconception = model.detect_misconception(
                topic,
                response.get('answer', ''),
                response.get('correct_answer', '')
            )
            if misconception:
                state['detected_misconception'] = misconception
    
    # Add student insights to state
    state['student_insights'] = {
        'topic': topic,
        'current_mastery': mastery,
        'recommended_difficulty': model.recommend_difficulty(topic),
        'needs_review': model.should_review(topic),
        'struggling': topic in model.struggling_topics,
        'misconceptions': model.misconceptions.get(topic, [])
    }
    
    # Update context for next interaction
    state['student_context'] = model.to_dict()
    
    return state


def _extract_topic_from_query(query: str) -> str:
    """Extract main topic from query (simplified)"""
    import re
    
    # Common COMP237 topics
    topics = [
        'dfs', 'bfs', 'a*', 'neural network', 'backpropagation', 'gradient descent',
        'supervised learning', 'unsupervised learning', 'classification', 'regression',
        'clustering', 'k-means', 'decision tree', 'random forest', 'svm',
        'precision', 'recall', 'f1 score', 'confusion matrix', 'overfitting',
        'regularization', 'cross-validation', 'feature engineering'
    ]
    
    query_lower = query.lower()
    for topic in topics:
        if topic in query_lower:
            return topic
    
    # Fallback: extract main noun phrase
    words = re.findall(r'\b[a-z]+\b', query_lower)
    if len(words) >= 2:
        return ' '.join(words[-2:])
    elif words:
        return words[-1]
    
    return 'general'


if __name__ == "__main__":
    # Test student model
    print("=" * 60)
    print("STUDENT MODEL TEST")
    print("=" * 60)
    
    # Simulate student interactions
    model = StudentModel()
    
    # First interaction: correct answer, no hints
    print("\n1. Student correctly answers DFS question (no hints)")
    model.update_mastery('dfs', {
        'correct': True,
        'confidence': 0.8,
        'time_taken': 45,
        'hint_level_used': 0
    })
    print(f"   DFS mastery: {model.estimate_mastery('dfs'):.2%}")
    print(f"   Recommended difficulty: {model.recommend_difficulty('dfs')}")
    
    # Second interaction: incorrect answer
    print("\n2. Student incorrectly answers neural networks (used hint 2)")
    model.update_mastery('neural networks', {
        'correct': False,
        'confidence': 0.3,
        'time_taken': 120,
        'hint_level_used': 2
    })
    print(f"   Neural networks mastery: {model.estimate_mastery('neural networks'):.2%}")
    print(f"   Struggling topics: {model.struggling_topics}")
    
    # Third interaction: improved performance
    print("\n3. Student correctly answers neural networks (hint 1)")
    model.update_mastery('neural networks', {
        'correct': True,
        'confidence': 0.6,
        'time_taken': 80,
        'hint_level_used': 1
    })
    print(f"   Neural networks mastery: {model.estimate_mastery('neural networks'):.2%}")
    
    # Check review schedule
    print("\n4. Review Schedule:")
    for topic, date in model.review_schedule.items():
        print(f"   {topic}: {date}")
    
    # Suggest next topics
    print("\n5. Suggested Next Topics:")
    topic_graph = {
        'backpropagation': ['neural networks', 'gradient descent'],
        'cnn': ['neural networks'],
        'a*': ['dfs', 'bfs']
    }
    suggestions = model.suggest_next_topics(topic_graph)
    for s in suggestions:
        print(f"   {s['topic']}: {s['reason']} (priority {s['priority']})")
