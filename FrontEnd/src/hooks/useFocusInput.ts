import { useEffect, useRef } from 'react';

/** Foca o input ao montar (teclado numérico no Android com inputMode). */
export function useFocusInput<T extends HTMLElement>(enabled = true) {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const el = ref.current;
    if (!el) return;

    const timer = window.setTimeout(() => {
      el.focus();
    }, 50);

    return () => window.clearTimeout(timer);
  }, [enabled]);

  return ref;
}
