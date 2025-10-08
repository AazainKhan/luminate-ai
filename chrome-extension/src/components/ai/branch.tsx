import React, { createContext, useContext, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

// Branch Context
interface BranchContextValue {
  currentBranch: number;
  totalBranches: number;
  onBranchChange: (index: number) => void;
}

const BranchContext = createContext<BranchContextValue | null>(null);

function useBranch() {
  const context = useContext(BranchContext);
  if (!context) {
    throw new Error('Branch components must be used within a Branch provider');
  }
  return context;
}

// Branch Provider Component
interface BranchProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultBranch?: number;
  totalBranches: number;
  onBranchChange?: (index: number) => void;
}

export function Branch({ 
  defaultBranch = 0, 
  totalBranches,
  onBranchChange,
  children,
  className,
  ...props 
}: BranchProps) {
  const [currentBranch, setCurrentBranch] = useState(defaultBranch);

  const handleBranchChange = useCallback((index: number) => {
    setCurrentBranch(index);
    onBranchChange?.(index);
  }, [onBranchChange]);

  return (
    <BranchContext.Provider value={{ currentBranch, totalBranches, onBranchChange: handleBranchChange }}>
      <div className={cn("relative", className)} {...props}>
        {children}
      </div>
    </BranchContext.Provider>
  );
}

// Branch Messages Container
interface BranchMessagesProps extends React.HTMLAttributes<HTMLDivElement> {}

export function BranchMessages({ children, className, ...props }: BranchMessagesProps) {
  const { currentBranch } = useBranch();
  
  // Render only the current branch
  const childArray = React.Children.toArray(children);
  const currentChild = childArray[currentBranch];

  return (
    <div className={cn("transition-opacity duration-200", className)} {...props}>
      {currentChild}
    </div>
  );
}

// Branch Selector Container
interface BranchSelectorProps extends React.HTMLAttributes<HTMLDivElement> {
  from?: 'user' | 'assistant' | 'system';
}

export function BranchSelector({ 
  from = 'assistant', 
  children, 
  className,
  ...props 
}: BranchSelectorProps) {
  const { totalBranches } = useBranch();
  
  // Don't render if only one branch
  if (totalBranches <= 1) {
    return null;
  }

  const alignClass = from === 'user' ? 'justify-end' : 'justify-start';

  return (
    <div 
      className={cn(
        "flex items-center gap-1 mt-2 text-xs text-muted-foreground",
        alignClass,
        className
      )} 
      {...props}
    >
      {children}
    </div>
  );
}

// Branch Previous Button
interface BranchPreviousProps extends React.ComponentProps<typeof Button> {}

export function BranchPrevious({ className, ...props }: BranchPreviousProps) {
  const { currentBranch, onBranchChange } = useBranch();
  const canGoPrevious = currentBranch > 0;

  const handlePrevious = useCallback(() => {
    if (canGoPrevious) {
      onBranchChange(currentBranch - 1);
    }
  }, [currentBranch, canGoPrevious, onBranchChange]);

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handlePrevious}
      disabled={!canGoPrevious}
      className={cn("h-6 w-6 p-0", className)}
      aria-label="Previous response"
      {...props}
    >
      <ChevronLeft className="h-3 w-3" />
    </Button>
  );
}

// Branch Next Button
interface BranchNextProps extends React.ComponentProps<typeof Button> {}

export function BranchNext({ className, ...props }: BranchNextProps) {
  const { currentBranch, totalBranches, onBranchChange } = useBranch();
  const canGoNext = currentBranch < totalBranches - 1;

  const handleNext = useCallback(() => {
    if (canGoNext) {
      onBranchChange(currentBranch + 1);
    }
  }, [currentBranch, canGoNext, totalBranches, onBranchChange]);

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleNext}
      disabled={!canGoNext}
      className={cn("h-6 w-6 p-0", className)}
      aria-label="Next response"
      {...props}
    >
      <ChevronRight className="h-3 w-3" />
    </Button>
  );
}

// Branch Page Indicator
interface BranchPageProps extends React.HTMLAttributes<HTMLSpanElement> {}

export function BranchPage({ className, ...props }: BranchPageProps) {
  const { currentBranch, totalBranches } = useBranch();

  return (
    <span 
      className={cn("px-2 font-mono text-xs", className)} 
      {...props}
    >
      {currentBranch + 1} / {totalBranches}
    </span>
  );
}

