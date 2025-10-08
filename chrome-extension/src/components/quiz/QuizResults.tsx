/**
 * QuizResults Component
 * Display quiz results with score and breakdown
 */

import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Progress } from '../ui/progress';
import { QuizSubmitResponse, QuizGenerateResponse } from '@/services/api';
import { QuizCard } from './QuizCard';
import { Trophy, RotateCcw, CheckCircle2, XCircle, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface QuizResultsProps {
  results: QuizSubmitResponse;
  quiz: QuizGenerateResponse;
  onRetry: () => void;
  onClose: () => void;
}

export function QuizResults({ results, quiz, onRetry, onClose }: QuizResultsProps) {
  const [showDetails, setShowDetails] = useState(false);

  const scorePercentage = results.score;
  const isPassing = scorePercentage >= 70;

  // Get performance level
  const getPerformanceLevel = () => {
    if (scorePercentage >= 90) return { label: 'Excellent!', color: 'text-green-600 dark:text-green-400' };
    if (scorePercentage >= 80) return { label: 'Great!', color: 'text-blue-600 dark:text-blue-400' };
    if (scorePercentage >= 70) return { label: 'Good', color: 'text-purple-600 dark:text-purple-400' };
    if (scorePercentage >= 60) return { label: 'Fair', color: 'text-yellow-600 dark:text-yellow-400' };
    return { label: 'Keep Trying', color: 'text-orange-600 dark:text-orange-400' };
  };

  const performance = getPerformanceLevel();

  return (
    <div className="space-y-6">
      {/* Score Header */}
      <div className="text-center space-y-4 py-6">
        <div className={cn(
          'inline-flex p-4 rounded-full',
          isPassing ? 'bg-green-100 dark:bg-green-900/30' : 'bg-orange-100 dark:bg-orange-900/30'
        )}>
          <Trophy className={cn(
            'h-12 w-12',
            isPassing ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'
          )} />
        </div>

        <div className="space-y-2">
          <h2 className="text-3xl font-bold">
            {Math.round(scorePercentage)}%
          </h2>
          <p className={cn('text-xl font-semibold', performance.color)}>
            {performance.label}
          </p>
        </div>

        <div className="flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span>{results.correct_count} Correct</span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <span>{results.total_questions - results.correct_count} Incorrect</span>
          </div>
        </div>
      </div>

      {/* Progress Visualization */}
      <Card className="p-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Your Score</span>
            <span>{results.correct_count}/{results.total_questions}</span>
          </div>
          <Progress value={scorePercentage} className="h-3" />
        </div>
      </Card>

      {/* Recommendations */}
      {!isPassing && (
        <Card className="p-4 bg-orange-50 dark:bg-orange-900/10 border-orange-200 dark:border-orange-800">
          <div className="flex gap-3">
            <TrendingUp className="h-5 w-5 text-orange-600 dark:text-orange-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-orange-900 dark:text-orange-100">
                Keep Learning!
              </h4>
              <p className="text-sm text-orange-700 dark:text-orange-300">
                Review the explanations below and try the quiz again. Practice makes perfect!
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Question Review Toggle */}
      <div className="flex justify-center">
        <Button
          variant="outline"
          onClick={() => setShowDetails(!showDetails)}
          className="w-full"
        >
          {showDetails ? 'Hide' : 'Show'} Detailed Breakdown
        </Button>
      </div>

      {/* Detailed Breakdown */}
      {showDetails && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Question Breakdown</h3>
          {quiz.questions.map((question, index) => {
            const result = results.results.find(r => r.question_id === question.id);
            if (!result) return null;

            return (
              <QuizCard
                key={question.id}
                question={question}
                selectedAnswer={result.selected}
                onSelect={() => {}}
                questionNumber={index + 1}
                totalQuestions={quiz.questions.length}
                showCorrectAnswer={true}
              />
            );
          })}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t">
        <Button
          variant="outline"
          onClick={onRetry}
          className="flex-1"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
        <Button
          onClick={onClose}
          className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
        >
          Finish
        </Button>
      </div>
    </div>
  );
}

