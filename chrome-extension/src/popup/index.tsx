import React from 'react';
import ReactDOM from 'react-dom/client';
import { DualModeChat } from '../components/DualModeChat';
import { ThemeProvider } from '../components/providers/theme-provider';
import '../index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <DualModeChat />
    </ThemeProvider>
  </React.StrictMode>
);
