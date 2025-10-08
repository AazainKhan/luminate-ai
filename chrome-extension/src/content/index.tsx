import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Sparkles, X } from 'lucide-react';
import { DualModeChat } from '../components/DualModeChat';
import './content.css';

// Main component for the injected button and chat
function LuminateButton() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    // Listen for messages from popup via window postMessage
    // (chrome.runtime is not available in page context)
    const handleMessage = (event: MessageEvent) => {
      // Only accept messages from the same origin
      if (event.origin !== window.location.origin) return;
      
      if (event.data?.type === 'LUMINATE_OPEN_CHAT') {
        setIsChatOpen(true);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <>
      {/* Sticky Button - positioned bottom right, to the left of Help button */}
      <button
        onClick={() => setIsChatOpen(!isChatOpen)}
        className="luminate-ai-button"
        style={{
          pointerEvents: 'auto',
          position: 'fixed',
          bottom: '20px',
          right: '128px', // 128px from right (left of Help button)
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          background: 'linear-gradient(to right, #2563eb, #4f46e5)',
          color: 'white',
          fontWeight: '500',
          fontSize: '14px',
          borderRadius: '9999px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          border: '2px solid rgba(255, 255, 255, 0.2)',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
          e.currentTarget.style.background = 'linear-gradient(to right, #1d4ed8, #4338ca)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)';
          e.currentTarget.style.background = 'linear-gradient(to right, #2563eb, #4f46e5)';
        }}
      >
        {isChatOpen ? (
          <>
            <X style={{ width: '20px', height: '20px' }} />
            <span>Close</span>
          </>
        ) : (
          <>
            <Sparkles style={{ width: '20px', height: '20px' }} />
            <span>Luminate AI</span>
          </>
        )}
      </button>

      {/* Chat Interface */}
      {isChatOpen && (
        <div 
          className="luminate-ai-chat-container"
          style={{
            pointerEvents: 'auto',
            position: 'fixed',
            right: 0,
            top: 0,
            height: '100vh',
            width: '384px',
            zIndex: 9999,
          }}
        >
          <DualModeChat onClose={() => setIsChatOpen(false)} />
        </div>
      )}
    </>
  );
}

// Main initialization
function init() {
  console.log('[Luminate AI] Content script initializing...');
  console.log('[Luminate AI] Current URL:', window.location.href);
  
  // Check if already initialized
  if (document.getElementById('luminate-ai-root')) {
    console.log('[Luminate AI] Already initialized, skipping');
    return;
  }

  // Create a container for our React app
  const container = document.createElement('div');
  container.id = 'luminate-ai-root';
  
  // Add some inline styles to ensure visibility
  container.style.position = 'fixed';
  container.style.zIndex = '999999';
  container.style.pointerEvents = 'none'; // Let clicks pass through container
  
  document.body.appendChild(container);
  
  console.log('[Luminate AI] Container created and appended to body');

  // Render the button
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <LuminateButton />
    </React.StrictMode>
  );

  console.log('[Luminate AI] React app rendered successfully!');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  console.log('[Luminate AI] DOM still loading, waiting for DOMContentLoaded...');
  document.addEventListener('DOMContentLoaded', init);
} else {
  console.log('[Luminate AI] DOM already loaded, initializing now...');
  init();
}

// Export for type safety
export {};
