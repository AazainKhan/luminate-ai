import { cn } from '@/lib/utils';
import { User, Bot, CheckCheck } from 'lucide-react';
import { ReactNode } from 'react';

interface MessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  children: ReactNode;
  timestamp?: Date;
  isStreaming?: boolean;
  mode?: 'navigate' | 'educate';
}

export function MessageBubble({ 
  role, 
  children, 
  timestamp,
  isStreaming = false,
  mode = 'navigate'
}: MessageBubbleProps) {
  const isUser = role === 'user';

  return (
    <div
      className={cn(
        "group flex w-full gap-4 px-6 py-4",
        isUser ? "justify-end bg-transparent" : "justify-start bg-transparent hover:bg-muted/30",
        "animate-in fade-in-0 duration-200 transition-colors"
      )}
    >
      {/* Avatar - Left for assistant only */}
      {!isUser && (
        <div className={cn(
          "flex h-7 w-7 shrink-0 select-none items-center justify-center rounded-md mt-1",
          mode === 'navigate' 
            ? "bg-blue-600/10 text-blue-600"
            : "bg-purple-600/10 text-purple-600"
        )}>
          <Bot className="h-4 w-4" />
        </div>
      )}

      {/* Message Content - Clean column, no boxes */}
      <div className={cn(
        "flex flex-col gap-1 flex-1 max-w-[calc(100%-3rem)]",
        isUser && "items-end"
      )}>
        {/* Clean message text - no bubble for assistant, subtle bubble for user */}
        <div className={cn(
          "w-full",
          isUser && "max-w-[80%] rounded-2xl bg-primary/90 text-primary-foreground px-4 py-2.5 shadow-sm"
        )}>
          {children}
          
          {/* Streaming indicator */}
          {isStreaming && !isUser && (
            <div className="mt-3 flex items-center gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/50" />
            </div>
          )}
        </div>

        {/* Timestamp - subtle, bottom-left */}
        {timestamp && !isUser && (
          <time className="px-1 text-[11px] text-muted-foreground/60">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </time>
        )}
      </div>
    </div>
  );
}


