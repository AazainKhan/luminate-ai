import { useEffect, useRef } from "react"

interface VisualizerProps {
  type: "mermaid" | "chart"
  data: string | any
  title?: string
}

export function Visualizer({ type, data, title }: VisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    if (type === "mermaid") {
      // For Mermaid diagrams, we'd need to load the Mermaid library
      // For now, display as code block
      containerRef.current.innerHTML = `<pre class="p-4 bg-gray-900 text-gray-100 rounded"><code>${data}</code></pre>`
    } else if (type === "chart") {
      // For charts, we'd use Recharts or similar
      // For now, display JSON data
      containerRef.current.innerHTML = `<pre class="p-4 bg-gray-50 border rounded"><code>${JSON.stringify(data, null, 2)}</code></pre>`
    }
  }, [type, data])

  return (
    <div className="border rounded-lg p-4 bg-white">
      {title && <h4 className="text-lg font-semibold mb-3">{title}</h4>}
      <div ref={containerRef} className="w-full"></div>
      <p className="text-xs text-gray-500 mt-2">
        Interactive visualization (Mermaid/Recharts integration coming soon)
      </p>
    </div>
  )
}

