import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { isThirdPartyStartTimeNoise } from './utils/safeTiming';
import './styles/globals.css';

/**
 * Extensões (React DevTools / analytics) injetam scripts VM* que leem
 * entry.startTime sem null-check. Isso gera TypeError no console sem
 * stack do nosso /src — não quebra a UI, mas polui o DevTools.
 * Em DEV, silenciamos apenas esse ruído de terceiro.
 */
if (import.meta.env.DEV && typeof window !== 'undefined') {
  window.addEventListener(
    'error',
    (ev) => {
      const stack =
        (ev.error && typeof ev.error === 'object' && 'stack' in ev.error
          ? String((ev.error as { stack?: string }).stack)
          : '') || ev.filename || '';
      if (isThirdPartyStartTimeNoise(String(ev.message ?? ''), stack)) {
        ev.preventDefault();
      }
    },
    true,
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <App />
    </BrowserRouter>
  </StrictMode>,
);
