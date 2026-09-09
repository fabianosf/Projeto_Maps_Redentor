/** Leitura segura de timing (evita crash em callbacks idle/performance). */

export type TimingLike = {
  startTime?: number | null;
} | null | undefined;

/** Nunca lê `.startTime` sem validar o objeto. */
export function readStartTime(obj: TimingLike): number | null {
  return obj?.startTime ?? null;
}

/** Filtra entradas indefinidas antes de ler startTime. */
export function readStartTimes(
  items: ReadonlyArray<TimingLike>,
): number[] {
  const out: number[] = [];
  for (const item of items) {
    const t = readStartTime(item);
    if (t != null && Number.isFinite(t)) out.push(t);
  }
  return out;
}

export function clearTimerSafe(id: number | null | undefined): void {
  if (id == null) return;
  window.clearTimeout(id);
  window.clearInterval(id);
}

export function cancelIdleCallbackSafe(id: number | null | undefined): void {
  if (id == null) return;
  const cancel = (
    window as Window & {
      cancelIdleCallback?: (handle: number) => void;
    }
  ).cancelIdleCallback;
  if (typeof cancel === 'function') {
    cancel(id);
    return;
  }
  window.clearTimeout(id);
}
