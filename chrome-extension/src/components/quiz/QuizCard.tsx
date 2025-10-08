/**
 * QuizCard Component
 * Display a single quiz question with options
 */

import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { QuizQuestion } from '@/services/api';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface QuizCardProps {
  question: QuizQuestion;
  selectedAnswer?: string;
  onSelect: (optionId: string) => void;
  questionNumber: number;
  totalQuestions: number;
  showCorrectAnswer?: boolean;
}

export function QuizCard({
  question,
  selectedAnswer,
  onSelect,
  questionNumber,
  totalQuestions,
  showCorrectAnswer = false,
}: QuizCardProps) {
  return (
    <Card className="p-6 space-y-4">
      {/* Question Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            Question {questionNumber} of {totalQuestions}
          </span>
          {showCorrectAnswer && selectedAnswer && (
            <span
              className={cn(
                'text-xs font-semibold px-2 py-1 rounded-full',
                selectedAnswer === question.correct_answer
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              )}
            >
              {selectedAnswer === question.correct_answer ? 'Correct' : 'Incorrect'}
            </span>
          )}
        </div>
        <h3 className="text-lg font-semibold leading-relaxed">{question.prompt}</h3>
      </div>

      {/* Options */}
      <div className="space-y-2">
        {question.options.map((option) => {
          const isSelected = selectedAnswer === option.id;
          const isCorrect = showCorrectAnswer && option.id === question.correct_answer;
          const isWrong = showCorrectAnswer && isSelected && option.id !== question.correct_answer;

          return (
            <Button
              key={option.id}
              variant="outline"
              className={cn(
                'w-full justify-start text-left h-auto py-3 px-4 transition-all',
                isSelected && !showCorrectAnswer && 'border-primary bg-primary/5',
                isCorrect && 'border-green-500 bg-green-50 dark:bg-green-900/20',
                isWrong && 'border-red-500 bg-red-50 dark:bg-red-900/20',
                !showCorrectAnswer && 'hover:bg-accent hover:border-accent-foreground/20'
              )}
              onClick={() => !showCorrectAnswer && onSelect(option.id)}
              disabled={showCorrectAnswer}
            >
              <div className="flex items-center gap-3 w-full">
                {/* Option Letter */}
                <div
                  className={cn(
                    'flex items-center justify-center w-6 h-6 rounded-full border-2 shrink-0 font-medium text-sm',
                    isSelected && !showCorrectAnswer && 'border-primary bg-primary text-primary-foreground',
                    isCorrect && 'border-green-500 bg-green-500 text-white',
                    isWrong && 'border-red-500 bg-red-500 text-white',
                    !isSelected && !showCorrectAnswer && 'border-muted-foreground/30'
                  )}
                >
                  {isCorrect ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    option.id.toUpperCase()
                  )}
                </div>

                {/* Option Text */}
                <span className="flex-1">{option.text}</span>
              </div>
            </Button>
          );
        })}
      </div>

      {/* Explanation (show if answer revealed) */}
      {showCorrectAnswer && selectedAnswer && (
        <div className="mt-4 p-4 rounded-lg bg-muted/50 border">
          <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <span className="h-1 w-1 rounded-full bg-primary"></span>
            Explanation
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {question.explanation}
          </p>
        </div>
      )}
    </Card>
  );
}

