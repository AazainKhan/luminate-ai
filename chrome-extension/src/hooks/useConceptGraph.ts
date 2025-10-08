/**
 * useConceptGraph Hook
 * Fetches and manages concept relationship graph data
 */

import { useState, useEffect, useCallback } from 'react';
import { fetchConceptGraph, ConceptGraph, ConceptNode, ConceptEdge } from '@/services/api';
import { getStudentId } from '@/utils/studentId';

interface GraphState {
  graph: ConceptGraph | null;
  isLoading: boolean;
  error: string | null;
  selectedNode: string | null;
  highlightedNodes: Set<string>;
}

export function useConceptGraph() {
  const [state, setState] = useState<GraphState>({
    graph: null,
    isLoading: true,
    error: null,
    selectedNode: null,
    highlightedNodes: new Set(),
  });

  /**
   * Load graph data
   */
  const load = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const studentId = await getStudentId();
      const graph = await fetchConceptGraph(studentId);

      setState(prev => ({
        ...prev,
        graph,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load concept graph',
      }));
    }
  }, []);

  /**
   * Initial load
   */
  useEffect(() => {
    load();
  }, [load]);

  /**
   * Select a node
   */
  const selectNode = (nodeId: string | null) => {
    if (!state.graph) return;

    if (!nodeId) {
      setState(prev => ({
        ...prev,
        selectedNode: null,
        highlightedNodes: new Set(),
      }));
      return;
    }

    // Find connected nodes
    const connected = new Set<string>();
    connected.add(nodeId);

    state.graph.edges.forEach(edge => {
      if (edge.source === nodeId) {
        connected.add(edge.target);
      } else if (edge.target === nodeId) {
        connected.add(edge.source);
      }
    });

    setState(prev => ({
      ...prev,
      selectedNode: nodeId,
      highlightedNodes: connected,
    }));
  };

  /**
   * Get node by ID
   */
  const getNode = (nodeId: string): ConceptNode | undefined => {
    return state.graph?.nodes.find(n => n.id === nodeId);
  };

  /**
   * Get connected nodes
   */
  const getConnectedNodes = (nodeId: string): ConceptNode[] => {
    if (!state.graph) return [];

    const connectedIds = new Set<string>();

    state.graph.edges.forEach(edge => {
      if (edge.source === nodeId) {
        connectedIds.add(edge.target);
      } else if (edge.target === nodeId) {
        connectedIds.add(edge.source);
      }
    });

    return state.graph.nodes.filter(n => connectedIds.has(n.id));
  };

  /**
   * Get prerequisites for a topic
   */
  const getPrerequisites = (nodeId: string): ConceptNode[] => {
    if (!state.graph) return [];

    const prereqIds = state.graph.edges
      .filter(edge => edge.target === nodeId && edge.type === 'prerequisite')
      .map(edge => edge.source);

    return state.graph.nodes.filter(n => prereqIds.includes(n.id));
  };

  /**
   * Get next steps from a topic
   */
  const getNextSteps = (nodeId: string): ConceptNode[] => {
    if (!state.graph) return [];

    const nextIds = state.graph.edges
      .filter(edge => edge.source === nodeId && edge.type === 'next_step')
      .map(edge => edge.target);

    return state.graph.nodes.filter(n => nextIds.includes(n.id));
  };

  /**
   * Get related topics
   */
  const getRelatedTopics = (nodeId: string): ConceptNode[] => {
    if (!state.graph) return [];

    const relatedIds = state.graph.edges
      .filter(
        edge =>
          (edge.source === nodeId || edge.target === nodeId) &&
          edge.type === 'related'
      )
      .map(edge => (edge.source === nodeId ? edge.target : edge.source));

    return state.graph.nodes.filter(n => relatedIds.includes(n.id));
  };

  /**
   * Get learning path (prerequisite chain)
   */
  const getLearningPath = (targetNodeId: string): ConceptNode[] => {
    if (!state.graph) return [];

    const path: ConceptNode[] = [];
    const visited = new Set<string>();
    const queue: string[] = [targetNodeId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      if (visited.has(currentId)) continue;
      visited.add(currentId);

      const node = getNode(currentId);
      if (node) {
        path.unshift(node);
      }

      // Add prerequisites to queue
      const prereqs = state.graph.edges
        .filter(
          edge => edge.target === currentId && edge.type === 'prerequisite'
        )
        .map(edge => edge.source);

      queue.push(...prereqs);
    }

    return path;
  };

  /**
   * Get mastery statistics
   */
  const getMasteryStats = () => {
    if (!state.graph) return { total: 0, mastered: 0, inProgress: 0, notStarted: 0 };

    const total = state.graph.nodes.length;
    const mastered = state.graph.nodes.filter(n => n.mastery >= 0.8).length;
    const inProgress = state.graph.nodes.filter(n => n.mastery > 0 && n.mastery < 0.8).length;
    const notStarted = state.graph.nodes.filter(n => n.mastery === 0).length;

    return { total, mastered, inProgress, notStarted };
  };

  /**
   * Find topics by module
   */
  const getByModule = (module: string): ConceptNode[] => {
    if (!state.graph) return [];
    return state.graph.nodes.filter(n => n.module === module);
  };

  return {
    // State
    graph: state.graph,
    isLoading: state.isLoading,
    error: state.error,
    selectedNode: state.selectedNode,
    highlightedNodes: state.highlightedNodes,

    // Actions
    load,
    selectNode,

    // Queries
    getNode,
    getConnectedNodes,
    getPrerequisites,
    getNextSteps,
    getRelatedTopics,
    getLearningPath,
    getMasteryStats,
    getByModule,
  };
}

