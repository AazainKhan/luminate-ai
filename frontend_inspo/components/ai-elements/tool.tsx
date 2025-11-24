"use client"

import { Wrench } from "lucide-react"

interface ToolProps {
  name: string
  args?: Record<string, any>
  result?: any
  status: "pending" | "in-progress" | "completed" | "error"
}

export function Tool({ name, args, result, status }: ToolProps) {
  return (
    <div className="my-3 rounded-lg border border-white/10 bg-white/5 p-3">
      <div className="flex items-center gap-2 mb-2">
        <Wrench className="h-4 w-4 text-purple-400" />
        <span className="text-sm font-medium text-white">{name}</span>
        <span
          className={`ml-auto text-xs px-2 py-0.5 rounded ${
            status === "completed"
              ? "bg-green-500/20 text-green-300"
              : status === "error"
                ? "bg-red-500/20 text-red-300"
                : status === "in-progress"
                  ? "bg-blue-500/20 text-blue-300"
                  : "bg-gray-500/20 text-gray-300"
          }`}
        >
          {status}
        </span>
      </div>
      {args && (
        <div className="mb-2">
          <div className="text-xs text-gray-400 mb-1">Arguments:</div>
          <pre className="text-xs bg-black/30 p-2 rounded overflow-x-auto">{JSON.stringify(args, null, 2)}</pre>
        </div>
      )}
      {result && (
        <div>
          <div className="text-xs text-gray-400 mb-1">Result:</div>
          <pre className="text-xs bg-black/30 p-2 rounded overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
