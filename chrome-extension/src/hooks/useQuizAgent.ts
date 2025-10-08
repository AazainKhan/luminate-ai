/**
 * useQuizAgent Hook
 * Manages quiz generation, state, and submission
 */

import { useState } from 'react';
import { generateQuiz, submitQuiz, QuizQuestion, QuizGenerateResponse, QuizSubmitResponse } from '@/services/api';
import { getStudentId } from '@/utils/studentId';

interface QuizState {
  quiz: QuizGenerateResponse | null;
  isGenerating: boolean;
  isSubmitting: boolean;
  currentQuestion: number;
  answers: Record<string, string>;
  results: QuizSubmitResponse | null;
  startTime: number | null;
  error: string | null;
}

export function useQuizAgent() {
  const [state, setState] = useState<QuizState>({
    quiz: null,
    isGenerating: false,
    isSubmitting: false,
    currentQuestion: 0,
    answers: {},
    results: null,
    startTime: null,
    error: null,
  });

  /**
   * Generate a new quiz
   */
  const generate = async (
    topic: string,
    difficulty: 'easy' | 'medium' | 'hard' = 'medium',
    count: number = 5
  ) => {
    setState(prev => ({ ...prev, isGenerating: true, error: null }));

    try {
      const quiz = await generateQuiz(topic, difficulty, count);
      setState(prev => ({
        ...prev,
        quiz,
        isGenerating: false,
        currentQuestion: 0,
        answers: {},
        results: null,
        startTime: Date.now(),
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isGenerating: false,
        error: error instanceof Error ? error.message : 'Failed to generate quiz',
      }));
    }
  };

  /**
   * Answer a question
   */
  const answerQuestion = (questionId: string, optionId: string) => {
    setState(prev => ({
      ...prev,
      answers: {
        ...prev.answers,
        [questionId]: optionId,
      },
    }));
  };

  /**
   * Go to next question
   */
  const nextQuestion = () => {
    setState(prev => ({
      ...prev,
      currentQuestion: Math.min(
        prev.currentQuestion + 1,
        (prev.quiz?.questions.length || 1) - 1
      ),
    }));
  };

  /**
   * Go to previous question
   */
  const prevQuestion = () => {
    setState(prev => ({
      ...prev,
      currentQuestion: Math.max(prev.currentQuestion - 1, 0),
    }));
  };

  /**
   * Submit the quiz
   */
  const submit = async () => {
    if (!state.quiz) return;

    setState(prev => ({ ...prev, isSubmitting: true, error: null }));

    try {
      const studentId = await getStudentId();
      const timeTaken = state.startTime ? Math.floor((Date.now() - state.startTime) / 1000) : undefined;

      const results = await submitQuiz(
        state.quiz.quiz_id,
        studentId,
        state.answers,
        timeTaken
      );

      setState(prev => ({
        ...prev,
        results,
        isSubmitting: false,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isSubmitting: false,
        error: error instanceof Error ? error.message : 'Failed to submit quiz',
      }));
    }
  };

  /**
   * Reset quiz
   */
  const reset = () => {
    setState({
      quiz: null,
      isGenerating: false,
      isSubmitting: false,
      currentQuestion: 0,
      answers: {},
      results: null,
      startTime: null,
      error: null,
    });
  };

  /**
   * Check if all questions are answered
   */
  const isComplete = () => {
    if (!state.quiz) return false;
    return state.quiz.questions.every(q => state.answers[q.id] !== undefined);
  };

  return {
    // State
    quiz: state.quiz,
    currentQuestion: state.currentQuestion,
    answers: state.answers,
    results: state.results,
    isGenerating: state.isGenerating,
    isSubmitting: state.isSubmitting,
    error: state.error,

    // Computed
    isComplete: isComplete(),
    progress: state.quiz ? (Object.keys(state.answers).length / state.quiz.questions.length) * 100 : 0,

    // Actions
    generate,
    answerQuestion,
    nextQuestion,
    prevQuestion,
    submit,
    reset,
  };
}

