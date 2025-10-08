import { useEffect, useState } from 'react';
import AgentPlan from '../ui/agent-plan';

interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  level: number;
  dependencies: string[];
  subtasks: Subtask[];
}

interface Subtask {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  tools?: string[];
}

interface StudyPlanViewerProps {
  studyPlanData?: any;
  planType?: 'weekly' | 'exam_prep' | 'topic_order';
  onTaskComplete?: (taskId: string) => void;
  onSubtaskComplete?: (taskId: string, subtaskId: string) => void;
}

/**
 * StudyPlanViewer - Visualizes study plans from backend as interactive tasks
 * 
 * Integrates with educate_graph.py study planner output:
 * - Weekly study plans → daily tasks
 * - Exam prep plans → week-by-week tasks
 * - Topic ordering → prerequisite-based task flow
 */
export function StudyPlanViewer({
  studyPlanData,
  planType = 'weekly',
  onTaskComplete,
  onSubtaskComplete,
}: StudyPlanViewerProps) {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    if (studyPlanData && studyPlanData.tasks) {
      setTasks(studyPlanData.tasks);
    }
  }, [studyPlanData]);

  const handleTaskStatusChange = (taskId: string, newStatus: string) => {
    if (newStatus === 'completed' && onTaskComplete) {
      onTaskComplete(taskId);
    }
  };

  const handleSubtaskStatusChange = (
    taskId: string,
    subtaskId: string,
    newStatus: string
  ) => {
    if (newStatus === 'completed' && onSubtaskComplete) {
      onSubtaskComplete(taskId, subtaskId);
    }
  };

  if (!tasks || tasks.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No study plan available. Ask me to create one!</p>
        <p className="text-xs mt-2">
          Try: "Create a study plan for this week" or "Plan my exam prep"
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-2 px-2">
        <h3 className="text-sm font-semibold text-foreground">
          {planType === 'weekly'
            ? '📅 Weekly Study Plan'
            : planType === 'exam_prep'
              ? '🎯 Exam Preparation Plan'
              : '📚 Topic Learning Path'}
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          Click tasks to expand, click checkboxes to mark complete
        </p>
      </div>
      <AgentPlan
        tasks={tasks}
        onTaskStatusChange={handleTaskStatusChange}
        onSubtaskStatusChange={handleSubtaskStatusChange}
      />
    </div>
  );
}
