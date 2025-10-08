/**
 * ConceptGraph Component
 * Simple visualization of concept relationships
 * Note: This is a simplified version. For production, consider using react-force-graph or D3.js
 */

import { useEffect, useRef, useState } from 'react';
import { useConceptGraph } from '@/hooks/useConceptGraph';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Loader2, RefreshCw, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ConceptGraph() {
  const graph = useConceptGraph();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const handleNodeClick = (nodeId: string) => {
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
      graph.selectNode(null);
    } else {
      setSelectedNodeId(nodeId);
      graph.selectNode(nodeId);
    }
  };

  if (graph.isLoading) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading concept graph...</p>
        </div>
      </div>
    );
  }

  if (graph.error) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <Card className="p-6 max-w-md text-center space-y-4">
          <p className="text-sm text-destructive">{graph.error}</p>
          <Button onClick={graph.load} variant="outline">
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  if (!graph.graph) return null;

  const masteryStats = graph.getMasteryStats();

  // Get mastery color
  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.8) return 'bg-green-500 border-green-600 text-white';
    if (mastery >= 0.5) return 'bg-yellow-500 border-yellow-600 text-white';
    if (mastery > 0) return 'bg-orange-500 border-orange-600 text-white';
    return 'bg-gray-300 border-gray-400 text-gray-700 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300';
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <GitBranch className="h-6 w-6" />
              Concept Map
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Explore topic relationships and prerequisites
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={graph.load}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3">
          <Card className="p-3 text-center">
            <div className="text-2xl font-bold">{masteryStats.total}</div>
            <div className="text-xs text-muted-foreground">Total Topics</div>
          </Card>
          <Card className="p-3 text-center bg-green-50 dark:bg-green-900/10">
            <div className="text-2xl font-bold text-green-700 dark:text-green-400">
              {masteryStats.mastered}
            </div>
            <div className="text-xs text-green-600 dark:text-green-500">Mastered</div>
          </Card>
          <Card className="p-3 text-center bg-yellow-50 dark:bg-yellow-900/10">
            <div className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">
              {masteryStats.inProgress}
            </div>
            <div className="text-xs text-yellow-600 dark:text-yellow-500">In Progress</div>
          </Card>
          <Card className="p-3 text-center bg-gray-50 dark:bg-gray-900/10">
            <div className="text-2xl font-bold text-gray-700 dark:text-gray-400">
              {masteryStats.notStarted}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-500">Not Started</div>
          </Card>
        </div>

        {/* Legend */}
        <Card className="p-4">
          <h3 className="text-sm font-semibold mb-3">Mastery Levels</h3>
          <div className="flex flex-wrap gap-3 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-green-500" />
              <span>Mastered (80%+)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-yellow-500" />
              <span>Good (50-79%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-orange-500" />
              <span>Learning (1-49%)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-gray-400 dark:bg-gray-600" />
              <span>Not Started</span>
            </div>
          </div>
        </Card>

        {/* Simplified Node List View */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold">Topics by Module</h3>
          
          {Object.entries(
            graph.graph.nodes.reduce((modules, node) => {
              const module = node.module || 'Other';
              if (!modules[module]) {
                modules[module] = [];
              }
              modules[module].push(node);
              return modules;
            }, {} as Record<string, typeof graph.graph.nodes>)
          ).map(([module, nodes]) => (
            <Card key={module} className="p-4">
              <h4 className="text-sm font-semibold mb-3">{module}</h4>
              <div className="space-y-2">
                {nodes.map((node) => {
                  const isSelected = selectedNodeId === node.id;
                  const isHighlighted = graph.highlightedNodes.has(node.id);
                  const prerequisites = graph.getPrerequisites(node.id);
                  const nextSteps = graph.getNextSteps(node.id);

                  return (
                    <div key={node.id}>
                      <Button
                        variant="outline"
                        className={cn(
                          'w-full justify-start h-auto py-2',
                          isSelected && 'ring-2 ring-primary',
                          isHighlighted && !isSelected && 'bg-accent'
                        )}
                        onClick={() => handleNodeClick(node.id)}
                      >
                        <div className="flex items-center gap-3 w-full">
                          <div
                            className={cn(
                              'w-3 h-3 rounded-full shrink-0',
                              getMasteryColor(node.mastery)
                            )}
                          />
                          <span className="flex-1 text-left">{node.label}</span>
                          <span className="text-xs text-muted-foreground">
                            {Math.round(node.mastery * 100)}%
                          </span>
                        </div>
                      </Button>

                      {/* Show connections when selected */}
                      {isSelected && (prerequisites.length > 0 || nextSteps.length > 0) && (
                        <div className="ml-6 mt-2 space-y-2 p-3 bg-muted/50 rounded-lg text-sm">
                          {prerequisites.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Prerequisites:
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {prerequisites.map((prereq) => (
                                  <span
                                    key={prereq.id}
                                    className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                                  >
                                    {prereq.label}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {nextSteps.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                Next Steps:
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {nextSteps.map((next) => (
                                  <span
                                    key={next.id}
                                    className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
                                  >
                                    {next.label}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

