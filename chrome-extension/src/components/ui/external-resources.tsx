import * as React from "react"
import { cva } from "class-variance-authority"
import { ExternalLink, Youtube, GraduationCap, ChevronDown, Globe, Loader2, BookOpen } from "lucide-react"
import { Button } from "./button"
import { fetchExternalResources } from "@/services/api"

import { cn } from "@/lib/utils"

const externalResourceVariants = cva(
  "group relative flex flex-col gap-2 rounded-lg border p-4 transition-all hover:shadow-md",
  {
    variants: {
      variant: {
        default: "border-border bg-card hover:border-primary/50",
        youtube: "border-red-200 bg-red-50/50 dark:border-red-900/30 dark:bg-red-950/20",
        oer: "border-blue-200 bg-blue-50/50 dark:border-blue-900/30 dark:bg-blue-950/20",
        educational: "border-purple-200 bg-purple-50/50 dark:border-purple-900/30 dark:bg-purple-950/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface ExternalResource {
  title: string
  url: string
  description?: string
  type: "YouTube Video" | "OER Commons" | "Khan Academy" | "MIT OCW" | string
  channel?: string
}

export interface ExternalResourcesProps
  extends React.HTMLAttributes<HTMLDivElement> {
  query: string  // Changed from resources to query for lazy loading
  title?: string
}

function getResourceIcon(type: string) {
  if (type.toLowerCase().includes("youtube")) {
    return <Youtube className="h-4 w-4 text-red-600 dark:text-red-400" />
  }
  if (type.toLowerCase().includes("wikipedia")) {
    return <Globe className="h-4 w-4 text-slate-600 dark:text-slate-400" />
  }
  if (type.toLowerCase().includes("khan")) {
    return <GraduationCap className="h-4 w-4 text-green-600 dark:text-green-400" />
  }
  if (type.toLowerCase().includes("oer")) {
    return <BookOpen className="h-4 w-4 text-blue-600 dark:text-blue-400" />
  }
  if (type.toLowerCase().includes("mit")) {
    return <GraduationCap className="h-4 w-4 text-purple-600 dark:text-purple-400" />
  }
  return <ExternalLink className="h-4 w-4 text-muted-foreground" />
}

function getResourceVariant(type: string): "youtube" | "oer" | "educational" | "default" {
  if (type.toLowerCase().includes("youtube")) return "youtube"
  if (type.toLowerCase().includes("oer") || type.toLowerCase().includes("wikipedia")) return "oer"
  if (type.toLowerCase().includes("khan") || type.toLowerCase().includes("mit")) return "educational"
  return "default"
}

const ExternalResources = React.forwardRef<
  HTMLDivElement,
  ExternalResourcesProps
>(({ className, query, title = "Load Additional Resources", ...props }, ref) => {
  const [isExpanded, setIsExpanded] = React.useState(false)
  const [resources, setResources] = React.useState<ExternalResource[]>([])
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  
  const handleLoadResources = async () => {
    if (isExpanded) {
      setIsExpanded(false)
      return
    }
    
    if (resources.length > 0) {
      setIsExpanded(true)
      return
    }
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetchExternalResources(query)
      setResources(response.resources)
      setIsExpanded(true)
    } catch (err) {
      console.error('Failed to load external resources:', err)
      setError('Failed to load resources. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      ref={ref}
      className={cn("flex flex-col gap-3", className)}
      {...props}
    >
      <Button
        variant="outline"
        size="sm"
        onClick={handleLoadResources}
        disabled={isLoading}
        className="w-full justify-between"
      >
        <div className="flex items-center gap-2">
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ExternalLink className="h-4 w-4" />
          )}
          <span className="text-sm font-medium">
            {isLoading ? "Loading..." : title}
          </span>
          {resources.length > 0 && (
            <span className="text-xs text-muted-foreground">
              ({resources.length} resources)
            </span>
          )}
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 transition-transform",
            isExpanded && "rotate-180"
          )}
        />
      </Button>
      
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
      
      {isExpanded && resources.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {resources.map((resource, index) => {
            const variant = getResourceVariant(resource.type)
            const icon = getResourceIcon(resource.type)
            
            return (
              <a
                key={index}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(externalResourceVariants({ variant }))}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {icon}
                    <span className="text-xs font-medium text-muted-foreground truncate">
                      {resource.type}
                    </span>
                  </div>
                  <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                
                <h4 className="text-sm font-semibold text-foreground line-clamp-2">
                  {resource.title}
                </h4>
                
                {resource.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {resource.description}
                  </p>
                )}
                
                {resource.channel && (
                  <p className="text-xs text-muted-foreground/80">
                    by {resource.channel}
                  </p>
                )}
              </a>
            )
          })}
        </div>
      )}
    </div>
  )
})

ExternalResources.displayName = "ExternalResources"

export { ExternalResources, externalResourceVariants }
