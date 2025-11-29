import { useEffect, RefObject } from "react"

export function useClickOutside<T extends HTMLElement = HTMLElement>(
  ref: RefObject<T>,
  handler: (event: MouseEvent | TouchEvent) => void
) {
  useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      const el = ref?.current
      const target = event.target as HTMLElement
      
      // Ignore if click is inside the ref element
      if (!el || el.contains(target as Node)) {
        return
      }

      // Ignore if click is inside a Radix UI Portal (Dropdowns, Tooltips, Dialogs, Selects)
      // Radix renders content into a portal at the body level
      if (
        target.closest('[data-radix-portal]') || 
        target.closest('[role="menu"]') || 
        target.closest('[role="listbox"]') ||
        target.closest('[role="dialog"]') ||
        target.closest('[data-radix-popper-content-wrapper]') ||
        target.closest('[data-radix-collection-item]') ||
        target.closest('[data-slot="select-content"]') ||
        target.closest('.radix-themes') // Catch-all for some themes
      ) {
        return
      }

      handler(event)
    }

    document.addEventListener("mousedown", listener)
    document.addEventListener("touchstart", listener)

    return () => {
      document.removeEventListener("mousedown", listener)
      document.removeEventListener("touchstart", listener)
    }
  }, [ref, handler])
}
