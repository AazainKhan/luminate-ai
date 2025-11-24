import { useState } from "react"
import { Copy, Play, Check, AlertCircle } from "lucide-react"
import { executeCode } from "~/lib/codeExecution"

interface CodeBlockProps {
  code: string
  language?: string
  onRun?: () => void
  showRunButton?: boolean
}

export function CodeBlock({ code, language = "python", onRun, showRunButton = true }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<{ stdout?: string; stderr?: string; error?: string } | null>(null)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRun = async () => {
    if (onRun) {
      // Use custom handler if provided
      setRunning(true)
      try {
        await onRun()
      } finally {
        setRunning(false)
      }
      return
    }

    // Default: execute via API
    if (language !== "python") {
      setResult({ error: "Only Python code can be executed" })
      return
    }

    setRunning(true)
    setResult(null)

    try {
      const execution_result = await executeCode({ code, language })
      
      if (execution_result.success) {
        setResult({
          stdout: execution_result.stdout,
          stderr: execution_result.stderr,
        })
      } else {
        setResult({
          error: execution_result.error || "Execution failed",
          stderr: execution_result.stderr,
        })
      }
    } catch (error: any) {
      setResult({
        error: error.message || "Failed to execute code",
      })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="border rounded-lg bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-xs font-mono text-gray-400 uppercase">{language}</span>
        <div className="flex items-center gap-2">
          {showRunButton && onRun && (
            <button
              onClick={handleRun}
              disabled={running}
              className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <Play className="w-3 h-3" />
              {running ? "Running..." : "Run"}
            </button>
          )}
          <button
            onClick={handleCopy}
            className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 flex items-center gap-1"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code */}
      <pre className="p-4 overflow-x-auto">
        <code className="text-sm text-gray-100 font-mono whitespace-pre">{code}</code>
      </pre>

      {/* Execution Result */}
      {result && (
        <div className="border-t border-gray-700 p-4 bg-gray-800">
          {result.error && (
            <div className="flex items-start gap-2 text-red-400 mb-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div className="text-sm">{result.error}</div>
            </div>
          )}
          {result.stderr && (
            <div className="text-red-400 text-sm font-mono mb-2 whitespace-pre-wrap">
              {result.stderr}
            </div>
          )}
          {result.stdout && (
            <div className="text-green-400 text-sm font-mono whitespace-pre-wrap">
              {result.stdout}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

