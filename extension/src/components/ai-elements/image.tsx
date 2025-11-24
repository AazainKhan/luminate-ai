"use client"

interface AIImageProps {
  src: string
  alt: string
  caption?: string
  className?: string
}

export function AIImage({ src, alt, caption, className }: AIImageProps) {
  return (
    <div className={`my-3 ${className || ""}`}>
      <img src={src || "/placeholder.svg"} alt={alt} className="rounded-lg border border-white/10 w-full" />
      {caption && <p className="mt-2 text-xs text-gray-400 text-center">{caption}</p>}
    </div>
  )
}
