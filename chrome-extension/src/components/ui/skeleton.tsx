/**
 * Skeleton loader components for better loading states
 */

import React from 'react';

export function MessageSkeleton() {
  return (
    <div className="animate-pulse space-y-3 p-4">
      <div className="h-4 bg-muted rounded w-3/4"></div>
      <div className="h-4 bg-muted rounded w-full"></div>
      <div className="h-4 bg-muted rounded w-5/6"></div>
    </div>
  );
}

export function SourcesSkeleton() {
  return (
    <div className="animate-pulse space-y-2 mt-4">
      <div className="h-3 bg-muted rounded w-24"></div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="border border-border rounded-lg p-3 space-y-2">
          <div className="h-4 bg-muted rounded w-2/3"></div>
          <div className="h-3 bg-muted rounded w-1/3"></div>
        </div>
      ))}
    </div>
  );
}

export function RelatedTopicsSkeleton() {
  return (
    <div className="animate-pulse space-y-2 mt-4">
      <div className="h-3 bg-muted rounded w-32"></div>
      <div className="flex gap-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-8 bg-muted rounded-full w-24"></div>
        ))}
      </div>
    </div>
  );
}

export function FullResponseSkeleton() {
  return (
    <div className="space-y-4">
      <MessageSkeleton />
      <SourcesSkeleton />
      <RelatedTopicsSkeleton />
    </div>
  );
}
