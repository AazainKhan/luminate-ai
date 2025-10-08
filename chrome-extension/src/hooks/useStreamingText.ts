import { useState, useEffect, useRef } from 'react';

/**
 * Hook to simulate character-by-character streaming for text responses
 * Provides a smooth streaming effect even when API returns complete text
 */
export function useStreamingText(
  finalText: string,
  enabled: boolean = true,
  speed: number = 20 // milliseconds per character
) {
  const [streamedText, setStreamedText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const indexRef = useRef(0);

  useEffect(() => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // If streaming is disabled, show full text immediately
    if (!enabled) {
      setStreamedText(finalText);
      setIsStreaming(false);
      return;
    }

    // If final text is empty, reset
    if (!finalText) {
      setStreamedText('');
      setIsStreaming(false);
      indexRef.current = 0;
      return;
    }

    // Start streaming
    setIsStreaming(true);
    indexRef.current = 0;
    setStreamedText('');

    intervalRef.current = setInterval(() => {
      if (indexRef.current < finalText.length) {
        setStreamedText(finalText.substring(0, indexRef.current + 1));
        indexRef.current++;
      } else {
        // Streaming complete
        setStreamedText(finalText);
        setIsStreaming(false);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    }, speed);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [finalText, enabled, speed]);

  const skipToEnd = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setStreamedText(finalText);
    setIsStreaming(false);
  };

  return {
    streamedText,
    isStreaming,
    skipToEnd,
  };
}


