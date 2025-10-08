/**
 * useDashboard Hook
 * Fetches and manages dashboard statistics
 */

import { useState, useEffect, useCallback } from 'react';
import { fetchDashboard, DashboardStats } from '@/services/api';
import { getStudentId } from '@/utils/studentId';

interface DashboardState {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useDashboard(autoRefresh: boolean = false) {
  const [state, setState] = useState<DashboardState>({
    stats: null,
    isLoading: true,
    error: null,
    lastUpdated: null,
  });

  /**
   * Fetch dashboard data
   */
  const refresh = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const studentId = await getStudentId();
      const stats = await fetchDashboard(studentId);

      setState({
        stats,
        isLoading: false,
        error: null,
        lastUpdated: new Date(),
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load dashboard',
      }));
    }
  }, []);

  /**
   * Initial load
   */
  useEffect(() => {
    refresh();
  }, [refresh]);

  /**
   * Auto-refresh if enabled
   */
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(refresh, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, [autoRefresh, refresh]);

  /**
   * Calculate learning streak
   */
  const getStreak = (): number => {
    return state.stats?.current_streak || 0;
  };

  /**
   * Get mastery percentage
   */
  const getMasteryPercentage = (): number => {
    if (!state.stats) return 0;
    // Assuming there are about 20 main topics in COMP-237
    const totalTopics = 20;
    return Math.round((state.stats.topics_mastered / totalTopics) * 100);
  };

  /**
   * Get quiz performance trend
   */
  const getQuizTrend = (): 'up' | 'down' | 'stable' => {
    if (!state.stats || state.stats.recent_activity.length < 2) return 'stable';

    const quizzes = state.stats.recent_activity
      .filter(activity => activity.type === 'quiz' && activity.score !== undefined)
      .slice(0, 5);

    if (quizzes.length < 2) return 'stable';

    const recent = quizzes.slice(0, 2).reduce((sum, q) => sum + (q.score || 0), 0) / 2;
    const older = quizzes.slice(2).reduce((sum, q) => sum + (q.score || 0), 0) / (quizzes.length - 2);

    if (recent > older + 5) return 'up';
    if (recent < older - 5) return 'down';
    return 'stable';
  };

  /**
   * Get next recommended topic
   */
  const getNextTopic = (): string | null => {
    return state.stats?.recommended_topics[0] || null;
  };

  /**
   * Check if student is on track
   */
  const isOnTrack = (): boolean => {
    if (!state.stats) return true;
    // Consider on track if average score >= 70 and has some mastery
    return state.stats.average_score >= 70 && state.stats.topics_mastered >= 3;
  };

  return {
    // State
    stats: state.stats,
    isLoading: state.isLoading,
    error: state.error,
    lastUpdated: state.lastUpdated,

    // Actions
    refresh,

    // Computed values
    streak: getStreak(),
    masteryPercentage: getMasteryPercentage(),
    quizTrend: getQuizTrend(),
    nextTopic: getNextTopic(),
    isOnTrack: isOnTrack(),
  };
}

