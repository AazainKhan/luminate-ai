import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChatInterface } from '../components/ChatInterface';
import '../index.css';

console.log('🚀 Side panel script loaded');

function SidePanel() {
  console.log('✅ SidePanel component rendering');
  return (
    <div style={{ 
      width: '100%', 
      height: '100vh',
      overflow: 'hidden',
      margin: 0,
      padding: 0
    }}>
      <ChatInterface onClose={() => {
        // Side panel doesn't need a close button - user can close via Chrome UI
        // But we keep the prop for compatibility
      }} />
    </div>
  );
}

try {
  const rootElement = document.getElementById('root');
  console.log('📍 Root element:', rootElement);
  
  if (!rootElement) {
    console.error('❌ Root element not found!');
  } else {
    const root = ReactDOM.createRoot(rootElement);
    console.log('✅ React root created');
    
    root.render(
      <React.StrictMode>
        <SidePanel />
      </React.StrictMode>
    );
    console.log('✅ React app rendered');
  }
} catch (error) {
  console.error('❌ Error rendering side panel:', error);
}
