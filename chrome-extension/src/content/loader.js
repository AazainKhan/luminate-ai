// Content script loader - injects the main module
// This works around Chrome's limitation with ES modules in content scripts

(function() {
  console.log('[Luminate AI Loader] Initializing...');
  
  // Listen for messages from the extension (e.g., popup)
  chrome.runtime.onMessage.addListener((message) => {
    console.log('[Luminate AI Loader] Received message:', message);
    if (message.action === 'OPEN_CHAT') {
      // Forward to the injected script via postMessage
      window.postMessage({ type: 'LUMINATE_OPEN_CHAT' }, window.location.origin);
    }
  });

  // Inject the main content script as an ES module
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('content.js');
  script.type = 'module';
  
  script.onload = () => {
    console.log('[Luminate AI Loader] Content script loaded successfully');
  };
  
  script.onerror = (error) => {
    console.error('[Luminate AI Loader] Failed to load content script:', error);
  };
  
  (document.head || document.documentElement).appendChild(script);
  console.log('[Luminate AI Loader] Script injected, waiting for load...');
})();
