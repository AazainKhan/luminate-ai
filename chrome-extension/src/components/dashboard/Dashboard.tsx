/**
 * Dashboard Component
 * Display student progress and statistics
 */

import { useDashboard } from '@/hooks/useDashboard';
import { ProgressCard } from './ProgressCard';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { RefreshCw, Trophy, Flame, Brain, TrendingUp, Target, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Dashboard() {
  const dashboard = useDashboard();

  if (dashboard.isLoading && !dashboard.stats) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (dashboard.error) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <Card className="p-6 max-w-md text-center space-y-4">
          <p className="text-sm text-destructive">{dashboard.error}</p>
          <Button onClick={dashboard.refresh} variant="outline">
            Try Again
          </Button>
        </Card>
      </div>
    );
  }

  const stats = dashboard.stats;
  if (!stats) return null;

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Your Progress</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Track your learning journey in COMP-237
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={dashboard.refresh}
            disabled={dashboard.isLoading}
          >
            <RefreshCw className={cn('h-4 w-4', dashboard.isLoading && 'animate-spin')} />
          </Button>
        </div>

        {/* On Track Status */}
        <Card className={cn(
          'p-4',
          dashboard.isOnTrack 
            ? 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-800'
            : 'bg-orange-50 border-orange-200 dark:bg-orange-900/10 dark:border-orange-800'
        )}>
          <div className="flex items-center gap-3">
            {dashboard.isOnTrack ? (
              <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
            ) : (
              <Target className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            )}
            <div>
              <p className={cn(
                'text-sm font-semibold',
                dashboard.isOnTrack 
                  ? 'text-green-900 dark:text-green-100'
                  : 'text-orange-900 dark:text-orange-100'
              )}>
                {dashboard.isOnTrack ? 'You\'re on track!' : 'Keep pushing forward!'}
              </p>
              <p className={cn(
                'text-xs',
                dashboard.isOnTrack
                  ? 'text-green-700 dark:text-green-300'
                  : 'text-orange-700 dark:text-orange-300'
              )}>
                {dashboard.isOnTrack 
                  ? 'Great job maintaining consistent progress'
                  : 'Review the recommended topics below to get back on track'}
              </p>
            </div>
          </div>
        </Card>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <ProgressCard
            icon={Trophy}
            label="Topics Mastered"
            value={stats.topics_mastered}
            color="text-yellow-600 dark:text-yellow-400"
            bgColor="bg-yellow-100 dark:bg-yellow-900/30"
            subtitle={`${dashboard.masteryPercentage}% complete`}
          />

          <ProgressCard
            icon={Flame}
            label="Current Streak"
            value={`${stats.current_streak} days`}
            color="text-orange-600 dark:text-orange-400"
            bgColor="bg-orange-100 dark:bg-orange-900/30"
            subtitle="Keep it going!"
          />

          <ProgressCard
            icon={Brain}
            label="Quizzes Taken"
            value={stats.total_quizzes}
            color="text-purple-600 dark:text-purple-400"
            bgColor="bg-purple-100 dark:bg-purple-900/30"
            subtitle={`${stats.average_score.toFixed(1)}% avg score`}
          />

          <ProgressCard
            icon={TrendingUp}
            label="Performance"
            value={dashboard.quizTrend === 'up' ? '📈' : dashboard.quizTrend === 'down' ? '📉' : '➡️'}
            color="text-blue-600 dark:text-blue-400"
            bgColor="bg-blue-100 dark:bg-blue-900/30"
            subtitle={
              dashboard.quizTrend === 'up' 
                ? 'Improving' 
                : dashboard.quizTrend === 'down' 
                ? 'Needs work' 
                : 'Stable'
            }
          />
        </div>

        {/* Weak Topics */}
        {stats.weak_topics.length > 0 && (
          <Card className="p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Target className="h-4 w-4 text-red-600 dark:text-red-400" />
              Areas for Improvement
            </h3>
            <div className="flex flex-wrap gap-2">
              {stats.weak_topics.map((topic) => (
                <span
                  key={topic}
                  className="px-3 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                >
                  {topic}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Recommended Topics */}
        {stats.recommended_topics.length > 0 && (
          <Card className="p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Brain className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              Recommended Next Topics
            </h3>
            <div className="flex flex-wrap gap-2">
              {stats.recommended_topics.map((topic) => (
                <span
                  key={topic}
                  className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                >
                  {topic}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Recent Activity */}
        {stats.recent_activity.length > 0 && (
          <Card className="p-4">
            <h3 className="text-sm font-semibold mb-3">Recent Activity</h3>
            <div className="space-y-2">
              {stats.recent_activity.slice(0, 5).map((activity, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                >
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{activity.topic}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {activity.score !== undefined && (
                      <span className="font-medium">{activity.score}%</span>
                    )}
                    <span>{new Date(activity.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

