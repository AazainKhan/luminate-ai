import { LucideIcon, Search, BookOpen, Video, FileText, Brain, Lightbulb, Calculator, Code } from 'lucide-react';

interface Suggestion {
  icon: LucideIcon;
  title: string;
  query: string;
  color: string;
}

interface StarterSuggestionsProps {
  suggestions: Suggestion[];
  onSelect: (query: string) => void;
}

export function StarterSuggestions({ suggestions, onSelect }: StarterSuggestionsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-4">
      {suggestions.map((suggestion, idx) => {
        const Icon = suggestion.icon;
        return (
          <button
            key={idx}
            onClick={() => onSelect(suggestion.query)}
            className={`group relative overflow-hidden rounded-lg border border-border/50 bg-card/50 p-4 text-left transition-all hover:border-${suggestion.color}-500/50 hover:bg-${suggestion.color}-500/5 hover:shadow-md hover:scale-[1.02] active:scale-[0.98]`}
          >
            <div className="flex items-start gap-3">
              <div className={`rounded-lg bg-${suggestion.color}-500/10 p-2 text-${suggestion.color}-500 transition-colors group-hover:bg-${suggestion.color}-500/20`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm text-foreground mb-1 group-hover:text-foreground/90">
                  {suggestion.title}
                </h3>
                <p className="text-xs text-muted-foreground line-clamp-2 group-hover:text-muted-foreground/80">
                  {suggestion.query}
                </p>
              </div>
            </div>
            <div className={`absolute inset-0 bg-gradient-to-br from-${suggestion.color}-500/0 via-${suggestion.color}-500/0 to-${suggestion.color}-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none`} />
          </button>
        );
      })}
    </div>
  );
}

// Predefined suggestion sets
export const NAVIGATE_SUGGESTIONS: Suggestion[] = [
  {
    icon: Search,
    title: 'Neural Networks',
    query: 'Show me content about neural networks',
    color: 'blue'
  },
  {
    icon: FileText,
    title: 'Week 3 Assignments',
    query: 'Find week 3 assignments',
    color: 'green'
  },
  {
    icon: BookOpen,
    title: 'Search Algorithms',
    query: 'Find resources on BFS and DFS algorithms',
    color: 'purple'
  },
  {
    icon: Video,
    title: 'Machine Learning Videos',
    query: 'Find video tutorials on machine learning basics',
    color: 'red'
  }
];

export const EDUCATE_SUGGESTIONS: Suggestion[] = [
  {
    icon: Calculator,
    title: 'Gradient Descent Formula',
    query: 'Explain gradient descent in 4 levels',
    color: 'blue'
  },
  {
    icon: Brain,
    title: 'Backpropagation',
    query: 'Walk me through backpropagation step by step',
    color: 'purple'
  },
  {
    icon: Code,
    title: 'Cross-Entropy Loss',
    query: 'Explain cross-entropy loss with code examples',
    color: 'green'
  },
  {
    icon: Lightbulb,
    title: 'Bayes Theorem',
    query: 'Break down Bayes theorem with real examples',
    color: 'amber'
  }
];


