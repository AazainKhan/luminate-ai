"use client";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export const TextGenerateEffect = ({
  words,
  className,
  filter = true,
  duration = 0.5,
}: {
  words: string;
  className?: string;
  filter?: boolean;
  duration?: number;
}) => {
  // Split words
  const wordsArray = words.split(" ");
  
  // State to track which words are visible
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    // Reset when words change
    setVisibleCount(0);
    
    const interval = setInterval(() => {
      setVisibleCount((prev) => {
        if (prev < wordsArray.length) {
          return prev + 1;
        }
        clearInterval(interval);
        return prev;
      });
    }, (duration * 1000) / 5); // Adjust speed based on duration

    return () => clearInterval(interval);
  }, [words, duration, wordsArray.length]);

  return (
    <div className={cn("font-normal", className)}>
      <div className="mt-4">
        <div className="dark:text-white text-black leading-snug tracking-wide">
          {wordsArray.map((word, idx) => {
            const isVisible = idx < visibleCount;
            return (
              <span
                key={word + idx}
                className="inline-block mr-1 transition-all duration-300"
                style={{
                  opacity: isVisible ? 1 : 0,
                  filter: filter ? (isVisible ? "blur(0px)" : "blur(10px)") : "none",
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};
