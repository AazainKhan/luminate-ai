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

interface LearningPathViewerProps {
  teachingStrategy?: string;
  interactionData?: any;
  topic?: string;
  onStepComplete?: (stepId: string) => void;
}

/**
 * LearningPathViewer - Visualizes pedagogical strategies as interactive task paths
 * 
 * Integrates with pedagogical_planner_agent output:
 * - Scaffolded hints → progressive hint reveal
 * - Worked examples → step-by-step solution
 * - Socratic dialogue → guided inquiry questions
 */
export function LearningPathViewer({
  teachingStrategy,
  interactionData,
  topic = 'Learning',
  onStepComplete,
}: LearningPathViewerProps) {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    if (interactionData && interactionData.tasks) {
      setTasks(interactionData.tasks);
    } else if (teachingStrategy) {
      // Fallback: generate simple task structure
      setTasks(generateDefaultTasks(teachingStrategy, topic));
    }
  }, [interactionData, teachingStrategy, topic]);

  const handleSubtaskStatusChange = (
    taskId: string,
    subtaskId: string,
    newStatus: string
  ) => {
    if (newStatus === 'completed' && onStepComplete) {
      onStepComplete(subtaskId);
    }
  };

  if (!tasks || tasks.length === 0) {
    return null;
  }

  return (
    <div className="w-full mt-4">
      <div className="mb-2 px-2">
        <h3 className="text-sm font-semibold text-foreground">
          📋 Learning Path
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          {getStrategyDescription(teachingStrategy)}
        </p>
      </div>
      <AgentPlan
        tasks={tasks}
        onSubtaskStatusChange={handleSubtaskStatusChange}
      />
    </div>
  );
}

function generateDefaultTasks(strategy?: string, topic?: string): Task[] {
  if (strategy === 'scaffolded_hints') {
    return [
      {
        id: '1',
        title: `Solve: ${topic}`,
        description: 'Progressive hints - try before revealing',
        status: 'in-progress',
        priority: 'high',
        level: 0,
        dependencies: [],
        subtasks: [
          {
            id: '1.1',
            title: 'Try solving on your own first',
            description: 'Attempt the problem before looking at hints',
            status: 'pending',
            priority: 'high',
          },
          {
            id: '1.2',
            title: 'Hint Level 1 (Light)',
            description: 'Click to reveal a guiding question',
            status: 'pending',
            priority: 'medium',
          },
          {
            id: '1.3',
            title: 'Hint Level 2 (Medium)',
            description: 'Click to reveal key concept explanation',
            status: 'pending',
            priority: 'medium',
          },
          {
            id: '1.4',
            title: 'Full Solution',
            description: 'Click to reveal complete explanation',
            status: 'pending',
            priority: 'low',
          },
        ],
      },
    ];
  } else if (strategy === 'worked_example') {
    return [
      {
        id: '1',
        title: `Worked Example: ${topic}`,
        description: 'Follow step-by-step solution',
        status: 'in-progress',
        priority: 'high',
        level: 0,
        dependencies: [],
        subtasks: [
          {
            id: '1.1',
            title: 'Step 1: Understand the problem',
            description: 'Read and analyze what is being asked',
            status: 'pending',
            priority: 'high',
          },
          {
            id: '1.2',
            title: 'Step 2: Plan approach',
            description: 'Identify which concepts and methods to use',
            status: 'pending',
            priority: 'medium',
          },
          {
            id: '1.3',
            title: 'Step 3: Execute solution',
            description: 'Apply the method step-by-step',
            status: 'pending',
            priority: 'medium',
          },
          {
            id: '1.4',
            title: 'Step 4: Verify result',
            description: 'Check the answer and reflect on the process',
            status: 'pending',
            priority: 'low',
          },
        ],
      },
    ];
  } else if (strategy === 'socratic_dialogue') {
    return [
      {
        id: '1',
        title: `Explore: ${topic}`,
        description: 'Discover through guided questions',
        status: 'in-progress',
        priority: 'high',
        level: 0,
        dependencies: [],
        subtasks: [
          {
            id: '1.1',
            title: 'What do you already know about this?',
            description: 'Reflect on prior knowledge',
            status: 'pending',
            priority: 'high',
          },
          {
            id: '1.2',
            title: 'Why is this concept important?',
            description: 'Consider the purpose and applications',
            status: 'pending',
            priority: 'medium',
          },
          {
            id: '1.3',
            title: 'How does this connect to other concepts?',
            description: 'Find relationships and patterns',
            status: 'pending',
            priority: 'medium',
          },
        ],
      },
    ];
  }

  return [];
}

function getStrategyDescription(strategy?: string): string {
  const descriptions: Record<string, string> = {
    scaffolded_hints: 'Progressive hints - reveal as needed',
    worked_example: 'Step-by-step solution walkthrough',
    socratic_dialogue: 'Guided inquiry through questions',
    quiz: 'Test your understanding',
    concept_map: 'Explore relationships between ideas',
    direct_explanation: 'Comprehensive explanation',
  };

  return descriptions[strategy || ''] || 'Follow the learning steps';
}
