import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Moon, Sun, LogIn, LogOut, User, X } from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Settings({ isOpen, onClose }: SettingsProps) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('luminate-theme') as 'light' | 'dark' || 'dark';
    setTheme(savedTheme);
    applyTheme(savedTheme);
  }, []);

  // Apply theme to document
  const applyTheme = (newTheme: 'light' | 'dark') => {
    const root = document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  // Toggle theme
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('luminate-theme', newTheme);
    applyTheme(newTheme);
  };

  // Mock login/logout (non-functional for now)
  const handleAuth = () => {
    setIsLoggedIn(!isLoggedIn);
    // TODO: Implement real authentication
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Settings Panel */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-80 bg-card border-l shadow-2xl z-50",
          "transform transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3 bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-violet-500/20 p-2">
              <SettingsIcon className="h-4 w-4 text-violet-600 dark:text-violet-400" />
            </div>
            <h2 className="font-semibold text-sm">Settings</h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Settings Content */}
        <div className="p-4 space-y-6">
          {/* Account Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Account
            </h3>
            
            {/* User Info (when logged in) */}
            {isLoggedIn && (
              <div className="flex items-center gap-3 p-3 rounded-lg border bg-accent/50">
                <div className="rounded-full bg-violet-500/20 p-2">
                  <User className="h-4 w-4 text-violet-600 dark:text-violet-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">Student User</p>
                  <p className="text-xs text-muted-foreground truncate">student@example.com</p>
                </div>
              </div>
            )}

            {/* Login/Logout Button */}
            <Button
              onClick={handleAuth}
              className={cn(
                "w-full justify-start gap-2",
                isLoggedIn
                  ? "bg-red-500/10 text-red-600 hover:bg-red-500/20 dark:text-red-400"
                  : "bg-violet-500/10 text-violet-600 hover:bg-violet-500/20 dark:text-violet-400"
              )}
              variant="ghost"
            >
              {isLoggedIn ? (
                <>
                  <LogOut className="h-4 w-4" />
                  <span>Log Out</span>
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  <span>Log In</span>
                </>
              )}
            </Button>
            
            {!isLoggedIn && (
              <p className="text-xs text-muted-foreground px-1">
                Login to sync your chat history and preferences.
              </p>
            )}
          </div>

          {/* Appearance Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Appearance
            </h3>
            
            {/* Theme Toggle */}
            <div className="flex items-center justify-between p-3 rounded-lg border bg-accent/50">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-amber-500/20 p-2">
                  {theme === 'light' ? (
                    <Sun className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                  ) : (
                    <Moon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium">Theme</p>
                  <p className="text-xs text-muted-foreground">
                    {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
                  </p>
                </div>
              </div>
              
              <Button
                onClick={toggleTheme}
                variant="outline"
                size="sm"
                className="h-8 px-3"
              >
                <div className="flex items-center gap-1.5">
                  {theme === 'light' ? (
                    <>
                      <Moon className="h-3 w-3" />
                      <span className="text-xs">Dark</span>
                    </>
                  ) : (
                    <>
                      <Sun className="h-3 w-3" />
                      <span className="text-xs">Light</span>
                    </>
                  )}
                </div>
              </Button>
            </div>
          </div>

          {/* About Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              About
            </h3>
            
            <div className="p-3 rounded-lg border bg-accent/50 space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <span className="text-white text-xs font-bold">L</span>
                </div>
                <div>
                  <p className="text-sm font-semibold">Luminate AI</p>
                  <p className="text-xs text-muted-foreground">v1.0.0</p>
                </div>
              </div>
              
              <div className="pt-2 border-t space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Navigate Mode:</span>
                  <span className="font-medium text-blue-600 dark:text-blue-400">Gemini 2.0 Flash</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Educate Mode:</span>
                  <span className="font-medium text-purple-600 dark:text-purple-400">Gemini 2.5 Flash</span>
                </div>
              </div>
            </div>
          </div>

          {/* Beta Notice */}
          <div className="p-3 rounded-lg border-2 border-dashed border-violet-500/30 bg-violet-500/5">
            <p className="text-xs text-center text-muted-foreground">
              🚀 <span className="font-semibold">Beta Version</span>
              <br />
              <span className="text-[10px]">COMP-237 AI Assistant</span>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
