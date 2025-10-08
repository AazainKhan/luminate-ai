/**
 * AgentBadge Component
 * Display agent attribution badge
 */

import { Brain, Search, FileText, Sparkles, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentBadgeProps {
  agent: string;
  className?: string;
}

const agentConfig: Record<string, { icon: typeof Brain; label: string; color: string }> = {
  query_understanding: {
    icon: Brain,
    label: 'Query Understanding',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  },
  retrieval: {
    icon: Search,
    label: 'Retrieval',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
  context: {
    icon: FileText,
    label: 'Context',
    color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  },
  formatting: {
    icon: Sparkles,
    label: 'Formatting',
    color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  },
  external_resources: {
    icon: Zap,
    label: 'External Resources',
    color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
  },
};

export function AgentBadge({ agent, className }: AgentBadgeProps) {
  const config = agentConfig[agent] || {
    icon: Brain,
    label: agent,
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
  };

  const Icon = config.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium',
        config.color,
        className
      )}
      title={config.label}
    >
      <Icon className="h-3 w-3" />
      <span>{config.label}</span>
    </div>
  );
}

