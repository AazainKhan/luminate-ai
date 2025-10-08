"use client"

import { useEffect } from 'react'
import { useLocalStorage } from './use-local-storage'

export function useDarkMode() {
  const [isDark, setIsDark] = useLocalStorage('dark-mode', false)

  useEffect(() => {
    const root = window.document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [isDark])

  const toggle = () => setIsDark(!isDark)

  return { isDark, toggle, setIsDark }
}
