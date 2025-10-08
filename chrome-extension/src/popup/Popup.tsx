import { useState, useEffect } from 'react';
import { Sparkles, BookOpen, Settings } from 'lucide-react';
import { cn } from '../lib/utils';

export function Popup() {
  const [isOnCoursePage, setIsOnCoursePage] = useState(false);

  useEffect(() => {
    // Check if we're on a Blackboard course page
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const url = tabs[0]?.url || '';
      const match = url.match(/\/ultra\/courses\/([^\/]+)\//);
      if (match) {
        setIsOnCoursePage(true);
      }
    });
  }, []);

  const openChat = () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id!, { action: 'OPEN_CHAT' });
      window.close();
    });
  };

  return (
    <div className="w-80 bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 text-white">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Luminate AI</h1>
            <p className="text-xs text-blue-100">COMP237 Course Assistant</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {isOnCoursePage ? (
          <>
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <div className="p-1.5 bg-green-100 rounded-full mt-0.5">
                  <BookOpen className="w-4 h-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">
                    Course Detected
                  </p>
                  <p className="text-xs text-green-700 mt-0.5">
                    Luminate AI is active on this course page
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={openChat}
              className={cn(
                "w-full py-3 px-4 rounded-lg font-medium",
                "bg-blue-600 hover:bg-blue-700 text-white",
                "flex items-center justify-center gap-2",
                "transition-colors duration-200",
                "shadow-sm hover:shadow-md"
              )}
            >
              <Sparkles className="w-5 h-5" />
              Open Course Assistant
            </button>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Features
              </h3>
              <div className="space-y-2 text-sm text-foreground">
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5" />
                  <p>Navigate course content with AI</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5" />
                  <p>Get explanations and related topics</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5" />
                  <p>Personalized learning recommendations</p>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="py-8 text-center">
            <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <BookOpen className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-sm font-semibold text-foreground mb-2">
              No Course Page Detected
            </h3>
            <p className="text-xs text-muted-foreground mb-4">
              Navigate to any Luminate Blackboard page to use Luminate AI
            </p>
            <p className="text-xs text-muted-foreground">
              Example: luminate.centennialcollege.ca/ultra/courses/_11378_1/outline
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="pt-4 border-t border-border">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>v1.0.0</span>
            <button className="flex items-center gap-1 hover:text-foreground transition-colors">
              <Settings className="w-3.5 h-3.5" />
              Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
