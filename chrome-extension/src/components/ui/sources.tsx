import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ExternalLink, BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

export interface Source {
  title: string
  module?: string
  url?: string
  relevance_explanation?: string
}

export interface SourcesProps extends React.HTMLAttributes<HTMLDivElement> {
  sources: Source[]
  title?: string
}

const Sources = React.forwardRef<HTMLDivElement, SourcesProps>(
  ({ className, sources, title = "Related Course Content", ...props }, ref) => {
    if (!sources || sources.length === 0) return null

    return (
      <div ref={ref} className={cn("space-y-3", className)} {...props}>
        <h4 className="text-sm font-semibold flex items-center gap-2">
          <BookOpen className="h-4 w-4" />
          {title}
        </h4>
        <div className="space-y-2">
          {sources.map((source, index) => (
            <Card 
              key={index} 
              className="hover:bg-accent/50 transition-colors cursor-pointer"
              onClick={() => {
                if (source.url) {
                  window.open(source.url, '_blank', 'noopener,noreferrer');
                }
              }}
            >
              <CardHeader className="p-4 pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 space-y-1">
                    <CardTitle className="text-sm font-medium line-clamp-2">
                      {source.title}
                    </CardTitle>
                    {source.module && (
                      <CardDescription className="text-xs">
                        {source.module}
                      </CardDescription>
                    )}
                  </div>
                  {source.url && (
                    <div className="shrink-0 text-primary">
                      <ExternalLink className="h-4 w-4" />
                    </div>
                  )}
                </div>
              </CardHeader>
              {source.relevance_explanation && (
                <CardContent className="p-4 pt-0">
                  <p className="text-xs text-muted-foreground">
                    {source.relevance_explanation}
                  </p>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </div>
    )
  }
)
Sources.displayName = "Sources"

export { Sources }
