/**
 * RF-05 — Cancelar (Web): encerra navegação e retorna à aba de origem quando possível.
 * Em mobile, prioriza history.back() (window.close() raramente é permitido).
 */
function isMobileBrowser(): boolean {
  return /Android|iPhone|iPad|iPod|Mobile|Mobi/i.test(navigator.userAgent);
}

function focusOpenerIfAvailable(): void {
  try {
    if (window.opener && !window.opener.closed) {
      window.opener.focus();
    }
  } catch {
    // opener cross-origin pode bloquear focus
  }
}

export function closeBrowserTabOrReturn(): void {
  focusOpenerIfAvailable();

  const goBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    }
  };

  const closeTab = () => {
    window.close();
  };

  if (isMobileBrowser()) {
    goBack();
    window.setTimeout(() => {
      if (!window.closed) closeTab();
    }, 150);
    return;
  }

  closeTab();
  window.setTimeout(() => {
    if (!window.closed) goBack();
  }, 150);
}
