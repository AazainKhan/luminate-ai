import { useState, FormEvent, KeyboardEvent, useRef } from 'react';
import { Send, Sparkles, StopCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { cn } from '@/lib/utils';

interface PromptInputProps {
  onSubmit: (message: { text?: string }) => void | Promise<void>;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
  mode?: 'navigate' | 'educate';
}

export function PromptInput({
  onSubmit,
  onStop,
  disabled = false,
  isStreaming = false,
  placeholder = 'Type your message...',
  mode = 'navigate',
}: PromptInputProps) {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    
    const value = input.trim();
    if (!value || isSubmitting || disabled || isStreaming) return;

    setIsSubmitting(true);
    setInput('');

    try {
      await onSubmit({ text: value });
    } finally {
      setIsSubmitting(false);
      // Focus back to textarea
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const modeColors = {
    navigate: 'focus-visible:ring-blue-500',
    educate: 'focus-visible:ring-purple-500',
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className={cn(
        "relative flex items-end gap-2 rounded-xl border bg-background p-3 transition-all",
        "focus-within:ring-2 focus-within:ring-offset-2",
        mode === 'navigate' ? "focus-within:ring-blue-500/20 border-blue-500/20" : "focus-within:ring-purple-500/20 border-purple-500/20"
      )}>
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isSubmitting || isStreaming}
            className={cn(
              "min-h-[60px] max-h-[200px] resize-none border-0 bg-transparent p-0 pr-12 focus-visible:ring-0 focus-visible:ring-offset-0",
              modeColors[mode]
            )}
            rows={2}
          />
          
          {/* Character count indicator */}
          {input.length > 0 && (
            <div className="absolute bottom-1 right-1 text-xs text-muted-foreground">
              {input.length}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          {isStreaming && onStop ? (
            <Button
              type="button"
              size="icon"
              onClick={onStop}
              variant="ghost"
              className="shrink-0 h-10 w-10 rounded-lg hover:bg-destructive/10 hover:text-destructive"
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isSubmitting || disabled || isStreaming}
              className={cn(
                "shrink-0 h-10 w-10 rounded-lg transition-all",
                mode === 'navigate' 
                  ? "bg-blue-600 hover:bg-blue-700 active:scale-95"
                  : "bg-purple-600 hover:bg-purple-700 active:scale-95",
                (!input.trim() || isSubmitting || disabled || isStreaming) && "opacity-50"
              )}
            >
              {isSubmitting ? (
                <Sparkles className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Hints */}
      <div className="mt-2 flex items-center justify-between px-1 text-xs text-muted-foreground">
        <span>Press <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono">Shift+Enter</kbd> for new line</span>
        {mode === 'navigate' && (
          <span className="text-blue-600 dark:text-blue-400">🔍 Fast Search Mode</span>
        )}
        {mode === 'educate' && (
          <span className="text-purple-600 dark:text-purple-400">🎓 Deep Learning Mode</span>
        )}
      </div>
    </form>
  );
}


