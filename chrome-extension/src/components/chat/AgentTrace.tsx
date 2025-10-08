/**
 * AgentTrace Component
 * Display agent execution steps in collapsible view
 */

import { useState } from 'react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { Button } from '../ui/button';
import { ChevronDown, ChevronRight, Activity } from 'lucide-react';
import { AgentBadge } from './AgentBadge';
import { cn } from '@/lib/utils';

interface AgentTraceProps {
  traces: Array<{
    agent: string;
    action: string;
    input?: any;
    output?: any;
    count?: number;
    timestamp?: string;
  }>;
  className?: string;
}

export function AgentTrace({ traces, className }: AgentTraceProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!traces || traces.length === 0) {
    return null;
  }

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn('rounded-lg border bg-muted/30', className)}
    >
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 h-auto py-2 px-3 hover:bg-muted/50"
        >
          {isOpen ? (
            <ChevronDown className="h-4 w-4 shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" />
          )}
          <Activity className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="text-sm font-medium">
            Agent Execution ({traces.length} step{traces.length > 1 ? 's' : ''})
          </span>
        </Button>
      </CollapsibleTrigger>

      <CollapsibleContent className="px-3 pb-3">
        <div className="space-y-2 mt-2">
          {traces.map((trace, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-2 rounded-md bg-background/50 border"
            >
              {/* Timeline dot */}
              <div className="flex flex-col items-center pt-1.5">
                <div className="h-2 w-2 rounded-full bg-primary" />
                {index < traces.length - 1 && (
                  <div className="h-full w-px bg-border mt-1" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 space-y-1.5">
                <div className="flex items-center gap-2">
                  <AgentBadge agent={trace.agent} />
                  {trace.timestamp && (
                    <span className="text-xs text-muted-foreground">
                      {new Date(trace.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>

                <p className="text-sm text-foreground">
                  {trace.action}
                  {trace.count !== undefined && (
                    <span className="text-muted-foreground ml-1">
                      ({trace.count} items)
                    </span>
                  )}
                </p>

                {/* Optional: Show input/output if available */}
                {trace.output && typeof trace.output === 'string' && (
                  <p className="text-xs text-muted-foreground font-mono bg-muted/50 p-2 rounded">
                    {trace.output.slice(0, 100)}
                    {trace.output.length > 100 && '...'}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

