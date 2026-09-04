import { useEffect } from 'react';

/** Aplica cor de fundo em html/body/#root/.app-shell só enquanto a tela estiver montada. */
export function useScreenBg(color: string) {
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const root = document.getElementById('root');
    const shell = document.querySelector('.app-shell') as HTMLElement | null;
    const prevHtml = html.style.backgroundColor;
    const prevBody = body.style.backgroundColor;
    const prevRoot = root?.style.backgroundColor ?? '';
    const prevShell = shell?.style.backgroundColor ?? '';
    html.style.backgroundColor = color;
    body.style.backgroundColor = color;
    if (root) root.style.backgroundColor = color;
    if (shell) shell.style.backgroundColor = color;
    return () => {
      html.style.backgroundColor = prevHtml;
      body.style.backgroundColor = prevBody;
      if (root) root.style.backgroundColor = prevRoot;
      if (shell) shell.style.backgroundColor = prevShell;
    };
  }, [color]);
}
