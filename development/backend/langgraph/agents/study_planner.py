"""
Study Planner Agent - Creates personalized study plans

Based on cognitive science principles:
- Spaced repetition (Ebbinghaus forgetting curve)
- Interleaving (mixing topics for better retention)
- Retrieval practice scheduling
- Prerequisite dependency mapping
- Exam preparation optimization

This agent creates ACTIONABLE study plans, not just lists.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class StudySession:
    """Represents a single study session"""
    date: str
    duration_minutes: int
    topic: str
    activity_type: str  # 'learn', 'practice', 'review', 'quiz', 'exam_prep'
    difficulty: str  # 'easy', 'medium', 'hard'
    materials: List[str]
    goals: List[str]
    prerequisites_met: bool
    priority: int  # 1-5, 1 is highest


class StudyPlanner:
    """
    Creates personalized study plans using cognitive science principles
    """
    
    def __init__(self, student_model: Any, course_structure: Dict[str, Any]):
        """
        Args:
            student_model: StudentModel instance with mastery data
            course_structure: {
                'topics': {topic_name: {prerequisites, difficulty, materials}},
                'assessments': [{name, date, topics_covered}]
            }
        """
        self.student_model = student_model
        self.course_structure = course_structure
        self.topic_graph = self._build_topic_graph()
    
    def create_exam_prep_plan(
        self,
        exam_date: str,
        exam_topics: List[str],
        available_hours_per_week: int = 10
    ) -> Dict[str, Any]:
        """
        Create optimized study plan for upcoming exam
        
        Uses:
        - Prerequisite ordering (learn foundations first)
        - Spaced repetition (review at optimal intervals)
        - Focus on weak areas (more time on low-mastery topics)
        - Cramming prevention (start early, distribute load)
        
        Returns:
            {
                'sessions': [StudySession],
                'timeline': {week: [sessions]},
                'coverage': {topic: hours_allocated},
                'recommendations': [str]
            }
        """
        exam_dt = datetime.fromisoformat(exam_date)
        days_until_exam = (exam_dt - datetime.now()).days
        
        if days_until_exam < 0:
            return {'error': 'Exam date has passed'}
        
        # Calculate available study time
        weeks_available = max(1, days_until_exam // 7)
        total_hours = weeks_available * available_hours_per_week
        
        # Analyze topic mastery and compute study needs
        topic_analysis = self._analyze_exam_topics(exam_topics)
        
        # Allocate time based on priority and gaps
        time_allocation = self._allocate_study_time(topic_analysis, total_hours)
        
        # Generate spaced repetition schedule
        sessions = self._generate_spaced_sessions(
            time_allocation,
            exam_date,
            available_hours_per_week
        )
        
        # Organize into weekly timeline
        timeline = self._create_weekly_timeline(sessions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            topic_analysis,
            days_until_exam,
            time_allocation
        )
        
        return {
            'sessions': [self._session_to_dict(s) for s in sessions],
            'timeline': timeline,
            'coverage': {t: a['hours'] for t, a in time_allocation.items()},
            'total_hours': total_hours,
            'weeks_until_exam': weeks_available,
            'days_until_exam': days_until_exam,
            'recommendations': recommendations,
            'readiness_score': self._calculate_readiness(exam_topics)
        }
    
    def create_weekly_plan(
        self,
        hours_available: int = 10,
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create balanced weekly study plan
        
        Principles:
        - Interleaving: Mix different topics in same week
        - Spaced repetition: Review due topics
        - Progressive difficulty: Easy → Hard within sessions
        - Balance: Learning new + reviewing old
        
        Returns:
            {
                'week_starting': str,
                'daily_sessions': {day: [StudySession]},
                'total_hours': int,
                'balance': {learn: %, review: %, practice: %}
            }
        """
        # Get topics due for review
        review_topics = [
            t for t in self.student_model.mastery_map.keys()
            if self.student_model.should_review(t)
        ]
        
        # Get new topics ready to learn (prerequisites met)
        new_topics = self._get_ready_topics(exclude=list(self.student_model.mastery_map.keys()))
        
        # Get struggling topics that need practice
        practice_topics = self.student_model.struggling_topics
        
        # Allocate time: 40% new, 30% review, 30% practice (research-backed ratio)
        hours_new = int(hours_available * 0.4)
        hours_review = int(hours_available * 0.3)
        hours_practice = hours_available - hours_new - hours_review
        
        sessions = []
        
        # Schedule review sessions (spaced repetition)
        for topic in review_topics[:3]:  # Top 3 due
            sessions.append(StudySession(
                date=(datetime.now() + timedelta(days=len(sessions) % 7)).isoformat(),
                duration_minutes=60,
                topic=topic,
                activity_type='review',
                difficulty='medium',
                materials=self._get_materials(topic),
                goals=[f'Refresh understanding of {topic}', 'Solve 3-5 practice problems'],
                prerequisites_met=True,
                priority=2
            ))
        
        # Schedule new learning (interleaved)
        if focus_areas:
            new_topics = [t for t in new_topics if t in focus_areas]
        
        for i, topic in enumerate(new_topics[:2]):
            sessions.append(StudySession(
                date=(datetime.now() + timedelta(days=(i+1)*2)).isoformat(),
                duration_minutes=90,
                topic=topic,
                activity_type='learn',
                difficulty=self.student_model.recommend_difficulty(topic),
                materials=self._get_materials(topic),
                goals=[
                    f'Understand core concepts of {topic}',
                    'Complete worked examples',
                    'Attempt 2 practice problems'
                ],
                prerequisites_met=True,
                priority=1
            ))
        
        # Schedule practice for struggling areas
        for topic in practice_topics[:2]:
            sessions.append(StudySession(
                date=(datetime.now() + timedelta(days=len(sessions) % 7 + 1)).isoformat(),
                duration_minutes=60,
                topic=topic,
                activity_type='practice',
                difficulty='medium',
                materials=self._get_materials(topic),
                goals=[
                    f'Strengthen understanding of {topic}',
                    'Identify and fix misconceptions',
                    'Solve 5-7 problems'
                ],
                prerequisites_met=True,
                priority=2
            ))
        
        # Organize by day
        daily_sessions = {}
        for session in sessions:
            day = datetime.fromisoformat(session.date).strftime('%A')
            if day not in daily_sessions:
                daily_sessions[day] = []
            daily_sessions[day].append(self._session_to_dict(session))
        
        # Calculate balance
        activity_counts = {'learn': 0, 'review': 0, 'practice': 0}
        for session in sessions:
            activity_counts[session.activity_type] += 1
        
        total = sum(activity_counts.values())
        balance = {k: f"{v/total*100:.0f}%" for k, v in activity_counts.items()}
        
        return {
            'week_starting': datetime.now().strftime('%Y-%m-%d'),
            'daily_sessions': daily_sessions,
            'total_hours': sum(s.duration_minutes for s in sessions) / 60,
            'balance': balance,
            'sessions': [self._session_to_dict(s) for s in sessions]
        }
    
    def optimize_topic_order(self, topics: List[str]) -> List[Dict[str, Any]]:
        """
        Order topics based on prerequisites and difficulty
        
        Uses topological sort on prerequisite graph
        
        Returns:
            [{topic, order, prerequisites, estimated_hours}]
        """
        # Build dependency graph
        graph = {t: self.topic_graph.get(t, []) for t in topics}
        
        # Topological sort (Kahn's algorithm)
        # in_degree = number of prerequisites (incoming edges)
        in_degree = {t: 0 for t in topics}
        for t in topics:
            for prereq in graph[t]:
                if prereq in in_degree:
                    in_degree[t] += 1  # Fixed: count incoming edges to t, not outgoing from prereq
        
        queue = [t for t in topics if in_degree[t] == 0]
        ordered = []
        
        while queue:
            topic = queue.pop(0)
            ordered.append(topic)
            
            # Reduce in-degree of dependents
            for dependent in topics:
                if topic in graph.get(dependent, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # Add metadata
        result = []
        for i, topic in enumerate(ordered):
            mastery = self.student_model.estimate_mastery(topic)
            difficulty = self._estimate_difficulty(topic)
            
            # Estimate hours needed (inverse of mastery, scaled by difficulty)
            base_hours = {'easy': 2, 'medium': 3, 'hard': 5}[difficulty]
            hours_needed = base_hours * (1 - mastery * 0.5)  # Mastery reduces time
            
            result.append({
                'topic': topic,
                'order': i + 1,
                'prerequisites': graph[topic],
                'estimated_hours': round(hours_needed, 1),
                'current_mastery': f"{mastery:.0%}",
                'difficulty': difficulty
            })
        
        return result
    
    def _analyze_exam_topics(self, topics: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze each topic's mastery and needs"""
        analysis = {}
        
        for topic in topics:
            mastery = self.student_model.estimate_mastery(topic)
            gaps = self.student_model.get_prerequisite_gaps(topic, self.topic_graph)
            
            # Priority: low mastery = high priority
            priority = 5 if mastery < 0.3 else (4 if mastery < 0.6 else 3)
            
            analysis[topic] = {
                'mastery': mastery,
                'gaps': gaps,
                'priority': priority,
                'needs_review': mastery > 0.3 and self.student_model.should_review(topic),
                'struggling': topic in self.student_model.struggling_topics
            }
        
        return analysis
    
    def _allocate_study_time(
        self,
        topic_analysis: Dict[str, Dict],
        total_hours: int
    ) -> Dict[str, Dict[str, float]]:
        """Allocate study hours based on need"""
        # Calculate weights (priority * inverse mastery)
        weights = {}
        for topic, data in topic_analysis.items():
            weight = data['priority'] * (1 - data['mastery'])
            weights[topic] = weight
        
        total_weight = sum(weights.values())
        
        # Allocate hours proportionally
        allocation = {}
        for topic, weight in weights.items():
            hours = (weight / total_weight) * total_hours
            allocation[topic] = {
                'hours': round(hours, 1),
                'sessions': max(1, int(hours / 1.5)),  # 1.5 hour sessions
                'priority': topic_analysis[topic]['priority']
            }
        
        return allocation
    
    def _generate_spaced_sessions(
        self,
        time_allocation: Dict[str, Dict],
        exam_date: str,
        hours_per_week: int
    ) -> List[StudySession]:
        """Generate sessions with spaced repetition"""
        sessions = []
        exam_dt = datetime.fromisoformat(exam_date)
        days_available = (exam_dt - datetime.now()).days
        
        # For each topic, create spaced sessions
        for topic, allocation in sorted(
            time_allocation.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        ):
            num_sessions = allocation['sessions']
            hours = allocation['hours']
            
            # Space sessions across available time (spaced repetition)
            if num_sessions == 1:
                # Single session: middle of study period
                session_day = days_available // 2
            else:
                # Multiple sessions: exponentially increasing intervals
                session_days = []
                for i in range(num_sessions):
                    # Exponential spacing: 1, 3, 7, 14 days apart
                    day = min(
                        days_available - 1,
                        int((days_available / num_sessions) * (i + 1))
                    )
                    session_days.append(day)
                
                for i, day in enumerate(session_days):
                    activity = 'learn' if i == 0 else 'review'
                    duration = int((hours / num_sessions) * 60)
                    
                    sessions.append(StudySession(
                        date=(datetime.now() + timedelta(days=day)).isoformat(),
                        duration_minutes=duration,
                        topic=topic,
                        activity_type=activity,
                        difficulty=self.student_model.recommend_difficulty(topic),
                        materials=self._get_materials(topic),
                        goals=self._generate_session_goals(topic, activity),
                        prerequisites_met=True,
                        priority=allocation['priority']
                    ))
        
        return sorted(sessions, key=lambda x: x.date)
    
    def _create_weekly_timeline(self, sessions: List[StudySession]) -> Dict[str, List[Dict]]:
        """Organize sessions into weekly timeline"""
        timeline = {}
        
        for session in sessions:
            date = datetime.fromisoformat(session.date)
            week = date.strftime('Week of %b %d')
            
            if week not in timeline:
                timeline[week] = []
            
            timeline[week].append(self._session_to_dict(session))
        
        return timeline
    
    def _generate_recommendations(
        self,
        topic_analysis: Dict,
        days_until_exam: int,
        time_allocation: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        # Time-based recommendations
        if days_until_exam < 7:
            recs.append("⚠️ URGENT: Less than 1 week until exam. Focus on review and practice problems.")
        elif days_until_exam < 14:
            recs.append("⏰ 2 weeks remaining: Balance new learning with intensive review.")
        else:
            recs.append("✅ Good time buffer: Focus on building strong foundations first.")
        
        # Mastery-based recommendations
        low_mastery_topics = [
            t for t, data in topic_analysis.items()
            if data['mastery'] < 0.3
        ]
        if low_mastery_topics:
            recs.append(
                f"📚 Priority topics (low mastery): {', '.join(low_mastery_topics[:3])}. "
                "Start with these immediately."
            )
        
        # Gap identification
        topics_with_gaps = [
            t for t, data in topic_analysis.items()
            if data['gaps']
        ]
        if topics_with_gaps:
            recs.append(
                f"🔗 Prerequisites needed: {topics_with_gaps[0]} requires mastery of "
                f"{', '.join(topic_analysis[topics_with_gaps[0]]['gaps'])} first."
            )
        
        # Study technique recommendations
        recs.append("💡 Use active recall: Test yourself before looking at answers.")
        recs.append("🔄 Spaced repetition: Review topics multiple times over days/weeks, not all at once.")
        
        return recs
    
    def _calculate_readiness(self, topics: List[str]) -> float:
        """Calculate exam readiness (0-100%)"""
        masteries = [self.student_model.estimate_mastery(t) for t in topics]
        return round(sum(masteries) / len(masteries) * 100, 1)
    
    def _get_ready_topics(self, exclude: List[str] = None) -> List[str]:
        """Get topics ready to learn (prerequisites met)"""
        exclude = exclude or []
        ready = []
        
        for topic, prereqs in self.topic_graph.items():
            if topic in exclude:
                continue
            
            if not prereqs or all(
                self.student_model.estimate_mastery(p) >= 0.6
                for p in prereqs
            ):
                ready.append(topic)
        
        return ready
    
    def _get_materials(self, topic: str) -> List[str]:
        """Get course materials for topic"""
        topic_data = self.course_structure.get('topics', {}).get(topic, {})
        return topic_data.get('materials', ['Course notes', 'Practice problems'])
    
    def _estimate_difficulty(self, topic: str) -> str:
        """Estimate topic difficulty"""
        topic_data = self.course_structure.get('topics', {}).get(topic, {})
        return topic_data.get('difficulty', 'medium')
    
    def _generate_session_goals(self, topic: str, activity: str) -> List[str]:
        """Generate specific session goals"""
        if activity == 'learn':
            return [
                f"Understand core concepts of {topic}",
                "Work through 2-3 examples",
                "Identify key formulas/algorithms"
            ]
        elif activity == 'review':
            return [
                f"Recall key concepts of {topic}",
                "Solve practice problems without notes",
                "Identify weak areas"
            ]
        else:  # practice
            return [
                f"Apply {topic} to new problems",
                "Achieve 80%+ accuracy on practice set",
                "Build speed and confidence"
            ]
    
    def _build_topic_graph(self) -> Dict[str, List[str]]:
        """Build prerequisite graph from course structure"""
        topics = self.course_structure.get('topics', {})
        return {
            topic: data.get('prerequisites', [])
            for topic, data in topics.items()
        }
    
    def _session_to_dict(self, session: StudySession) -> Dict[str, Any]:
        """Convert session to dict"""
        return {
            'date': session.date,
            'duration_minutes': session.duration_minutes,
            'topic': session.topic,
            'activity_type': session.activity_type,
            'difficulty': session.difficulty,
            'materials': session.materials,
            'goals': session.goals,
            'priority': session.priority
        }


def study_planner_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate study plan based on request
    
    Handles:
    - "create study plan for exam on [date]"
    - "plan my week"
    - "what should I study next"
    """
    from .student_model import StudentModel
    
    query = state.get('query', '').lower()
    student_context = state.get('student_context', {})
    
    # Load student model
    model = StudentModel(student_context)
    
    # Load course structure (mock for now - should come from DB)
    course_structure = _get_comp237_structure()
    
    planner = StudyPlanner(model, course_structure)
    
    # Detect plan type
    if 'exam' in query or 'test' in query or 'midterm' in query or 'final' in query:
        # Extract date if provided
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
        exam_date = date_match.group(1) if date_match else (
            datetime.now() + timedelta(days=14)
        ).isoformat()
        
        # Extract topics (simplified)
        all_topics = list(course_structure['topics'].keys())
        exam_topics = all_topics  # Should parse from query
        
        plan = planner.create_exam_prep_plan(exam_date, exam_topics)
        state['study_plan'] = plan
        state['plan_type'] = 'exam_prep'
    
    elif 'week' in query or 'this week' in query:
        plan = planner.create_weekly_plan()
        state['study_plan'] = plan
        state['plan_type'] = 'weekly'
    
    elif 'order' in query or 'sequence' in query or 'what next' in query:
        topics = list(course_structure['topics'].keys())
        plan = planner.optimize_topic_order(topics)
        state['study_plan'] = {'ordered_topics': plan}
        state['plan_type'] = 'topic_order'
    
    else:
        # Default: weekly plan
        plan = planner.create_weekly_plan()
        state['study_plan'] = plan
        state['plan_type'] = 'weekly'
    
    return state


def _get_comp237_structure() -> Dict[str, Any]:
    """Mock course structure (should load from database)"""
    return {
        'topics': {
            'dfs': {
                'prerequisites': [],
                'difficulty': 'medium',
                'materials': ['Week 3 Notes', 'DFS Visualization', 'Practice Problems']
            },
            'bfs': {
                'prerequisites': [],
                'difficulty': 'medium',
                'materials': ['Week 3 Notes', 'BFS Visualization']
            },
            'a*': {
                'prerequisites': ['dfs', 'bfs'],
                'difficulty': 'hard',
                'materials': ['Week 4 Notes', 'A* Examples']
            },
            'neural networks': {
                'prerequisites': [],
                'difficulty': 'hard',
                'materials': ['Week 6 Notes', 'Neural Network Simulator']
            },
            'backpropagation': {
                'prerequisites': ['neural networks'],
                'difficulty': 'hard',
                'materials': ['Week 7 Notes', 'Backprop Derivation']
            }
        }
    }


if __name__ == "__main__":
    from student_model import StudentModel
    
    print("=" * 60)
    print("STUDY PLANNER TEST")
    print("=" * 60)
    
    # Create student with some history
    model = StudentModel()
    model.mastery_map = {
        'dfs': 0.7,
        'bfs': 0.6,
        'neural networks': 0.3
    }
    model.struggling_topics = ['neural networks']
    
    course = _get_comp237_structure()
    planner = StudyPlanner(model, course)
    
    # Test 1: Exam prep plan
    print("\n1. EXAM PREP PLAN (2 weeks until exam)")
    exam_date = (datetime.now() + timedelta(days=14)).isoformat()
    plan = planner.create_exam_prep_plan(
        exam_date,
        ['dfs', 'bfs', 'a*', 'neural networks'],
        available_hours_per_week=10
    )
    
    print(f"\nTotal Hours: {plan['total_hours']}")
    print(f"Readiness Score: {plan['readiness_score']}%")
    print(f"\nCoverage:")
    for topic, hours in plan['coverage'].items():
        print(f"  {topic}: {hours} hours")
    
    print(f"\nRecommendations:")
    for rec in plan['recommendations']:
        print(f"  {rec}")
    
    # Test 2: Weekly plan
    print("\n\n2. WEEKLY STUDY PLAN")
    weekly = planner.create_weekly_plan()
    print(f"\nBalance: {weekly['balance']}")
    print(f"Total Hours: {weekly['total_hours']}")
    print(f"\nDaily Sessions:")
    for day, sessions in weekly['daily_sessions'].items():
        print(f"\n  {day}:")
        for s in sessions:
            print(f"    - {s['topic']} ({s['activity_type']}, {s['duration_minutes']}min)")
    
    # Test 3: Topic ordering
    print("\n\n3. OPTIMAL TOPIC ORDER")
    ordered = planner.optimize_topic_order(['a*', 'dfs', 'bfs', 'backpropagation', 'neural networks'])
    for item in ordered:
        print(f"  {item['order']}. {item['topic']} ({item['estimated_hours']}h, {item['current_mastery']} mastery)")
        if item['prerequisites']:
            print(f"     Prerequisites: {', '.join(item['prerequisites'])}")
