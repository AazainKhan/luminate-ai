"""
Helper functions to convert backend intelligent logic outputs
into AgentPlan task format for frontend visualization.

Converts study plans, quiz progress, and learning strategies
into hierarchical tasks/subtasks for the agent-plan component.
"""

from typing import Dict, List, Any
from datetime import datetime


def study_plan_to_tasks(study_plan: Dict[str, Any], plan_type: str = 'weekly') -> List[Dict[str, Any]]:
    """
    Convert study planner output to AgentPlan tasks format.
    
    Args:
        study_plan: Output from study_planner_agent
        plan_type: 'weekly', 'exam_prep', or 'topic_order'
        
    Returns:
        List of tasks with subtasks in AgentPlan format
    """
    tasks = []
    
    if plan_type == 'weekly':
        tasks = _convert_weekly_plan(study_plan)
    elif plan_type == 'exam_prep':
        tasks = _convert_exam_prep_plan(study_plan)
    elif plan_type == 'topic_order':
        tasks = _convert_topic_order(study_plan)
    
    return tasks


def _convert_weekly_plan(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert weekly study plan to tasks"""
    daily_sessions = plan.get('daily_sessions', {})
    
    tasks = []
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for task_id, day in enumerate(day_order, start=1):
        if day not in daily_sessions:
            continue
            
        sessions = daily_sessions[day]
        
        # Calculate day status based on sessions
        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.get('status') == 'completed')
        
        if completed_sessions == total_sessions:
            day_status = 'completed'
        elif completed_sessions > 0:
            day_status = 'in-progress'
        else:
            day_status = 'pending'
        
        # Create subtasks from sessions
        subtasks = []
        for subtask_id, session in enumerate(sessions, start=1):
            subtask = {
                'id': f"{task_id}.{subtask_id}",
                'title': session.get('topic', 'Study Session'),
                'description': f"{session.get('duration_minutes', 60)} min - {', '.join(session.get('goals', []))}",
                'status': session.get('status', 'pending'),
                'priority': session.get('priority', 'medium'),
                'tools': session.get('materials', [])
            }
            subtasks.append(subtask)
        
        # Create day task
        task = {
            'id': str(task_id),
            'title': f"{day} Study Plan",
            'description': f"{len(sessions)} sessions - {sum(s.get('duration_minutes', 60) for s in sessions)} total minutes",
            'status': day_status,
            'priority': 'medium',
            'level': 0,
            'dependencies': [],
            'subtasks': subtasks
        }
        tasks.append(task)
    
    return tasks


def _convert_exam_prep_plan(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert exam prep plan to tasks"""
    timeline = plan.get('timeline', {})
    coverage = plan.get('coverage', {})
    
    tasks = []
    
    # Group by week
    for task_id, (week_key, sessions) in enumerate(sorted(timeline.items()), start=1):
        # Calculate week status
        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.get('status') == 'completed')
        
        if completed_sessions == total_sessions:
            week_status = 'completed'
        elif completed_sessions > 0:
            week_status = 'in-progress'
        else:
            week_status = 'pending'
        
        # Create subtasks from sessions
        subtasks = []
        for subtask_id, session in enumerate(sessions, start=1):
            topic = session.get('topic', 'Topic')
            activity = session.get('activity_type', 'study')
            
            subtask = {
                'id': f"{task_id}.{subtask_id}",
                'title': f"{activity.title()}: {topic}",
                'description': f"{session.get('duration_minutes', 60)} min - {session.get('difficulty', 'medium')} difficulty",
                'status': session.get('status', 'pending'),
                'priority': _priority_to_string(session.get('priority', 3)),
                'tools': session.get('materials', [])
            }
            subtasks.append(subtask)
        
        # Calculate total hours for week
        total_hours = sum(s.get('duration_minutes', 60) for s in sessions) / 60
        
        task = {
            'id': str(task_id),
            'title': f"Week {task_id} - Exam Prep",
            'description': f"{len(sessions)} sessions - {total_hours:.1f} hours total",
            'status': week_status,
            'priority': 'high',
            'level': 0,
            'dependencies': [str(task_id - 1)] if task_id > 1 else [],
            'subtasks': subtasks
        }
        tasks.append(task)
    
    return tasks


def _convert_topic_order(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert prerequisite-ordered topics to tasks"""
    ordered_topics = plan.get('ordered_topics', [])
    
    tasks = []
    
    for topic_data in ordered_topics:
        topic = topic_data.get('topic', 'Topic')
        order = topic_data.get('order', 1)
        prerequisites = topic_data.get('prerequisites', [])
        estimated_hours = topic_data.get('estimated_hours', 3)
        mastery = topic_data.get('current_mastery', '0%')
        difficulty = topic_data.get('difficulty', 'medium')
        
        # Determine status based on mastery
        mastery_percent = int(mastery.rstrip('%'))
        if mastery_percent >= 80:
            status = 'completed'
        elif mastery_percent >= 40:
            status = 'in-progress'
        else:
            status = 'pending'
        
        # Create learning subtasks
        subtasks = [
            {
                'id': f"{order}.1",
                'title': f"Learn {topic} fundamentals",
                'description': f"Study core concepts - {estimated_hours * 0.4:.1f} hours",
                'status': 'completed' if mastery_percent >= 80 else 'in-progress' if mastery_percent >= 20 else 'pending',
                'priority': _difficulty_to_priority(difficulty),
                'tools': ['Course materials', 'Video tutorials']
            },
            {
                'id': f"{order}.2",
                'title': f"Practice {topic} problems",
                'description': f"Solve practice problems - {estimated_hours * 0.4:.1f} hours",
                'status': 'completed' if mastery_percent >= 80 else 'in-progress' if mastery_percent >= 60 else 'pending',
                'priority': _difficulty_to_priority(difficulty),
                'tools': ['Practice problems', 'Quiz generator']
            },
            {
                'id': f"{order}.3",
                'title': f"Master {topic} applications",
                'description': f"Apply to real problems - {estimated_hours * 0.2:.1f} hours",
                'status': 'completed' if mastery_percent >= 80 else 'pending',
                'priority': _difficulty_to_priority(difficulty),
                'tools': ['Projects', 'Case studies']
            }
        ]
        
        # Find prerequisite task IDs
        prereq_ids = []
        for prereq_topic in prerequisites:
            # Find the order/ID of prerequisite topic
            for other in ordered_topics:
                if other.get('topic') == prereq_topic:
                    prereq_ids.append(str(other.get('order', 0)))
                    break
        
        task = {
            'id': str(order),
            'title': f"{topic} ({mastery})",
            'description': f"{difficulty.title()} - ~{estimated_hours:.1f} hours needed",
            'status': status,
            'priority': _difficulty_to_priority(difficulty),
            'level': len(prerequisites),  # Level based on prerequisite depth
            'dependencies': prereq_ids,
            'subtasks': subtasks
        }
        tasks.append(task)
    
    return tasks


def quiz_progress_to_tasks(quiz_data: Dict[str, Any], student_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert quiz generator output to tasks (question progression).
    
    Args:
        quiz_data: Output from quiz_generator_agent
        student_insights: Output from student_model_agent
        
    Returns:
        List of quiz tasks
    """
    questions = quiz_data.get('questions', [])
    topic = quiz_data.get('topic', 'Quiz')
    
    tasks = []
    
    # Group questions by difficulty
    by_difficulty = {'easy': [], 'medium': [], 'hard': []}
    for q in questions:
        diff = q.get('difficulty', 'medium')
        by_difficulty[diff].append(q)
    
    task_id = 1
    for difficulty in ['easy', 'medium', 'hard']:
        if not by_difficulty[difficulty]:
            continue
            
        difficulty_questions = by_difficulty[difficulty]
        
        # Create subtasks for each question
        subtasks = []
        for subtask_id, question in enumerate(difficulty_questions, start=1):
            subtask = {
                'id': f"{task_id}.{subtask_id}",
                'title': question.get('question', 'Question')[:50] + '...',
                'description': f"Bloom's: {question.get('blooms_level', 'Apply')} - {question.get('points', 10)} points",
                'status': question.get('status', 'pending'),
                'priority': difficulty,
                'tools': [f"Hint {i+1}" for i in range(len(question.get('hints', [])))]
            }
            subtasks.append(subtask)
        
        # Calculate task status
        completed = sum(1 for q in difficulty_questions if q.get('status') == 'completed')
        if completed == len(difficulty_questions):
            status = 'completed'
        elif completed > 0:
            status = 'in-progress'
        else:
            status = 'pending'
        
        task = {
            'id': str(task_id),
            'title': f"{difficulty.title()} Questions - {topic}",
            'description': f"{len(difficulty_questions)} questions - Test your understanding",
            'status': status,
            'priority': difficulty,
            'level': 0,
            'dependencies': [str(task_id - 1)] if task_id > 1 else [],
            'subtasks': subtasks
        }
        tasks.append(task)
        task_id += 1
    
    return tasks


def teaching_strategy_to_tasks(
    teaching_strategy: str,
    interaction_prompts: Dict[str, Any],
    topic: str
) -> List[Dict[str, Any]]:
    """
    Convert pedagogical strategy to learning tasks.
    
    Args:
        teaching_strategy: Strategy name (scaffolded_hints, worked_example, etc.)
        interaction_prompts: Prompts from pedagogical_planner_agent
        topic: Topic being taught
        
    Returns:
        List of learning tasks
    """
    if teaching_strategy == 'scaffolded_hints':
        return _hints_to_tasks(interaction_prompts, topic)
    elif teaching_strategy == 'worked_example':
        return _worked_example_to_tasks(interaction_prompts, topic)
    elif teaching_strategy == 'socratic_dialogue':
        return _socratic_to_tasks(interaction_prompts, topic)
    else:
        # Default: single task with explanation
        return [{
            'id': '1',
            'title': f"Learn {topic}",
            'description': f"Direct explanation - {teaching_strategy}",
            'status': 'in-progress',
            'priority': 'medium',
            'level': 0,
            'dependencies': [],
            'subtasks': []
        }]


def _hints_to_tasks(prompts: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
    """Convert scaffolded hints to progressive tasks"""
    hints = prompts.get('hints', [])
    
    subtasks = []
    for i, hint in enumerate(hints, start=1):
        subtask = {
            'id': f"1.{i}",
            'title': f"Hint Level {i}",
            'description': hint.get('text', hint) if isinstance(hint, dict) else hint,
            'status': 'pending',
            'priority': 'medium',
            'tools': []
        }
        subtasks.append(subtask)
    
    return [{
        'id': '1',
        'title': f"Solve {topic} with Hints",
        'description': "Progressive hints - try before revealing",
        'status': 'in-progress',
        'priority': 'high',
        'level': 0,
        'dependencies': [],
        'subtasks': subtasks
    }]


def _worked_example_to_tasks(prompts: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
    """Convert worked example to step-by-step tasks"""
    steps = prompts.get('steps', [])
    
    subtasks = []
    for i, step in enumerate(steps, start=1):
        subtask = {
            'id': f"1.{i}",
            'title': f"Step {i}: {step.get('title', step)}" if isinstance(step, dict) else f"Step {i}",
            'description': step.get('explanation', step) if isinstance(step, dict) else str(step),
            'status': 'pending',
            'priority': 'medium',
            'tools': []
        }
        subtasks.append(subtask)
    
    return [{
        'id': '1',
        'title': f"Worked Example: {topic}",
        'description': "Follow step-by-step solution",
        'status': 'in-progress',
        'priority': 'high',
        'level': 0,
        'dependencies': [],
        'subtasks': subtasks
    }]


def _socratic_to_tasks(prompts: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
    """Convert Socratic questions to guided inquiry tasks"""
    questions = prompts.get('questions', [])
    
    subtasks = []
    for i, question in enumerate(questions, start=1):
        subtask = {
            'id': f"1.{i}",
            'title': question.get('question', question) if isinstance(question, dict) else question,
            'description': f"Think deeply about this question",
            'status': 'pending',
            'priority': 'medium',
            'tools': []
        }
        subtasks.append(subtask)
    
    return [{
        'id': '1',
        'title': f"Explore {topic} Through Questions",
        'description': "Socratic dialogue - discover through inquiry",
        'status': 'in-progress',
        'priority': 'high',
        'level': 0,
        'dependencies': [],
        'subtasks': subtasks
    }]


# Helper functions

def _priority_to_string(priority: int) -> str:
    """Convert numeric priority (1-5) to string (high/medium/low)"""
    if priority <= 2:
        return 'high'
    elif priority <= 3:
        return 'medium'
    else:
        return 'low'


def _difficulty_to_priority(difficulty: str) -> str:
    """Convert difficulty to priority"""
    mapping = {
        'easy': 'low',
        'medium': 'medium',
        'hard': 'high'
    }
    return mapping.get(difficulty, 'medium')
