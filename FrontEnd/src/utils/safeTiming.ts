/** Leitura segura de timing (evita crash em callbacks idle/performance). */

export type TimingLike = {
  startTime?: number | null;
} | null | undefined;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object';
}

/** Nunca lê `.startTime` sem validar o objeto. */
export function readStartTime(obj: TimingLike | unknown): number | null {
  if (!isRecord(obj)) return null;
  const raw = obj.startTime;
  if (typeof raw !== 'number' || !Number.isFinite(raw)) return null;
  return raw;
}

/** Filtra entradas indefinidas antes de ler startTime. */
export function readStartTimes(
  items: ReadonlyArray<TimingLike | unknown> | null | undefined,
): number[] {
  if (!Array.isArray(items)) return [];
  const out: number[] = [];
  for (const item of items) {
    const t = readStartTime(item);
    if (t != null) out.push(t);
  }
  return out;
}

/**
 * Lê PerformanceEntry[] com segurança.
 * Scripts de extensão (ex.: reportAllChanges em VM*) às vezes passam undefined.
 */
export function readPerformanceEntryStartTimes(
  entries: ReadonlyArray<PerformanceEntry | null | undefined> | null | undefined,
): number[] {
  return readStartTimes(entries);
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

/**
 * Identifica ruído típico de extensão/DevTools (VM104, reportAllChanges),
 * não proveniente de arquivos do app em /src/.
 */
export function isThirdPartyStartTimeNoise(
  message: string,
  stack?: string | null,
): boolean {
  const msg = String(message ?? '');
  if (!/startTime|reportAllChanges/i.test(msg)) return false;
  const st = String(stack ?? '');
  if (/chrome-extension:|moz-extension:|safari-extension:/i.test(st)) return true;
  if (/VM\d+/i.test(st) && !/\/src\//i.test(st)) return true;
  // Stack minificado anônimo sem arquivo do projeto.
  if (!st.trim() || (/<anonymous>|unknown script/i.test(st) && !/\/src\//i.test(st))) {
    return true;
  }
  return false;
}
