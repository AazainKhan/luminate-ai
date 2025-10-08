/**
 * QuizDialog Component
 * Modal dialog for taking quizzes
 */

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { useQuizAgent } from '@/hooks/useQuizAgent';
import { QuizCard } from './QuizCard';
import { QuizResults } from './QuizResults';
import { Loader2, X } from 'lucide-react';

interface QuizDialogProps {
  open: boolean;
  onClose: () => void;
  topic: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  questionCount?: number;
}

export function QuizDialog({
  open,
  onClose,
  topic,
  difficulty = 'medium',
  questionCount = 5,
}: QuizDialogProps) {
  const quiz = useQuizAgent();

  // Generate quiz when dialog opens
  React.useEffect(() => {
    if (open && !quiz.quiz) {
      quiz.generate(topic, difficulty, questionCount);
    }
  }, [open, topic]);

  const handleClose = () => {
    quiz.reset();
    onClose();
  };

  const handleSubmit = async () => {
    await quiz.submit();
  };

  const currentQuestion = quiz.quiz?.questions[quiz.currentQuestion];

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        {quiz.isGenerating ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">Generating quiz questions...</p>
          </div>
        ) : quiz.results ? (
          <QuizResults
            results={quiz.results}
            quiz={quiz.quiz!}
            onRetry={() => {
              quiz.reset();
              quiz.generate(topic, difficulty, questionCount);
            }}
            onClose={handleClose}
          />
        ) : quiz.quiz ? (
          <>
            <DialogHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <DialogTitle className="text-xl">Quiz: {quiz.quiz.topic}</DialogTitle>
                  <DialogDescription>
                    Difficulty: {quiz.quiz.difficulty} • {quiz.quiz.questions.length} questions
                  </DialogDescription>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleClose}
                  className="h-8 w-8 rounded-full"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </DialogHeader>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Progress</span>
                <span>{Math.round(quiz.progress)}% Complete</span>
              </div>
              <Progress value={quiz.progress} className="h-2" />
            </div>

            {/* Question */}
            {currentQuestion && (
              <QuizCard
                question={currentQuestion}
                selectedAnswer={quiz.answers[currentQuestion.id]}
                onSelect={(optionId) => quiz.answerQuestion(currentQuestion.id, optionId)}
                questionNumber={quiz.currentQuestion + 1}
                totalQuestions={quiz.quiz.questions.length}
              />
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={quiz.prevQuestion}
                disabled={quiz.currentQuestion === 0}
              >
                Previous
              </Button>

              <span className="text-sm text-muted-foreground">
                Question {quiz.currentQuestion + 1} of {quiz.quiz.questions.length}
              </span>

              {quiz.currentQuestion < quiz.quiz.questions.length - 1 ? (
                <Button
                  onClick={quiz.nextQuestion}
                  disabled={!quiz.answers[currentQuestion?.id || '']}
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={!quiz.isComplete || quiz.isSubmitting}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  {quiz.isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Quiz'
                  )}
                </Button>
              )}
            </div>

            {/* Error Message */}
            {quiz.error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
                {quiz.error}
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-sm text-muted-foreground">Failed to generate quiz</p>
            <Button
              onClick={() => quiz.generate(topic, difficulty, questionCount)}
              className="mt-4"
            >
              Try Again
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// Need to import React for useEffect
import React from 'react';

