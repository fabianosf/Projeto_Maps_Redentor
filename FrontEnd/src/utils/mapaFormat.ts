/** Código operacional do MAPA (ex.: Red01). Nunca usa id interno / 00001. */
export function formatCodMap(
  _cod?: number | string | null | undefined,
  codigoMapa?: string | null,
): string {
  return formatCodigoMapa(codigoMapa);
}

/** Exibe apenas `codigo_mapa` da API. */
export function formatCodigoMapa(codigoMapa?: string | null): string {
  const c = String(codigoMapa ?? '').trim();
  if (c && /^[A-Za-z]/.test(c)) return c;
  return '—';
}

/** Extrai HH:MM de datetime ISO / SQL. */
export function formatHora(value: string | null | undefined): string {
  if (!value) return '—';
  const s = String(value);
  const m = s.match(/(\d{2}):(\d{2})/);
  return m ? `${m[1]}:${m[2]}` : s;
}

/** Extrai YYYY-MM-DD a partir de string, Date ou serializações comuns da API. */
export function toDateInput(value: string | number | Date | null | undefined): string {
  if (value == null || value === '') return '';
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    const y = value.getFullYear();
    const m = String(value.getMonth() + 1).padStart(2, '0');
    const d = String(value.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  const s = String(value).trim();
  if (!s || s.toLowerCase() === 'null' || s.toLowerCase() === 'invalid date') return '';
  // 2026-08-03 | 2026-08-03 13:00:00 | 2026-08-03T13:00:00
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  // dd/mm/aaaa
  const br = s.match(/^(\d{2})\/(\d{2})\/(\d{4})/);
  if (br) return `${br[3]}-${br[2]}-${br[1]}`;
  // Timestamp('2026-08-03 ...') vindo de serialização ruim
  const ts = s.match(/(\d{4}-\d{2}-\d{2})/);
  if (ts) return ts[1];
  const parsed = Date.parse(s);
  if (!Number.isNaN(parsed)) {
    const dt = new Date(parsed);
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const d = String(dt.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }
  return '';
}

/** YYYY-MM-DD ou ISO → dd/mm/aaaa */
export function toDateBR(value: string | null | undefined): string {
  const ymd = toDateInput(value);
  if (!ymd) return '';
  const [y, m, d] = ymd.split('-');
  return `${d}/${m}/${y}`;
}

/** Data de hoje em dd/mm/aaaa */
export function todayBR(): string {
  const now = new Date();
  const d = String(now.getDate()).padStart(2, '0');
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const y = String(now.getFullYear());
  return `${d}/${m}/${y}`;
}

/** Valida e normaliza dd/mm/aaaa → dd/mm/aaaa ou null */
export function parseDateBR(value: string): string | null {
  const m = value.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const dd = Number(m[1]);
  const mm = Number(m[2]);
  const yyyy = Number(m[3]);
  const dt = new Date(yyyy, mm - 1, dd);
  if (
    dt.getFullYear() !== yyyy ||
    dt.getMonth() !== mm - 1 ||
    dt.getDate() !== dd
  ) {
    return null;
  }
  return `${m[1]}/${m[2]}/${m[3]}`;
}

/** dd/mm/aaaa → YYYY-MM-DD para API */
export function brToYmd(value: string): string {
  const ok = parseDateBR(value);
  if (!ok) return '';
  const [d, m, y] = ok.split('/');
  return `${y}-${m}-${d}`;
}

/** Valida HH:MM */
export function isValidHHMM(value: string): boolean {
  const m = value.trim().match(/^(\d{2}):(\d{2})$/);
  if (!m) return false;
  const hh = Number(m[1]);
  const mm = Number(m[2]);
  return hh >= 0 && hh <= 23 && mm >= 0 && mm <= 59;
}

/** Converte para valor de datetime-local (YYYY-MM-DDTHH:MM). */
export function toDateTimeLocal(value: string | null | undefined): string {
  if (!value) return '';
  const s = String(value).trim();
  const iso = s.replace(' ', 'T').match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})/);
  if (iso) return `${iso[1]}T${iso[2]}:${iso[3]}`;

  // Flask/RFC (ex.: "Fri, 04 Sep 2026 10:00:00 GMT") — UTC bate com formatHora (HH:MM literal).
  const d = new Date(s);
  if (!Number.isNaN(d.getTime())) {
    const pad = (n: number) => String(n).padStart(2, '0');
    const useUtc = /GMT|UTC|\bZ\b/i.test(s) || /,\s*\d{2}\s+\w{3}\s+\d{4}/.test(s);
    const y = useUtc ? d.getUTCFullYear() : d.getFullYear();
    const m = useUtc ? d.getUTCMonth() + 1 : d.getMonth() + 1;
    const day = useUtc ? d.getUTCDate() : d.getDate();
    const hh = useUtc ? d.getUTCHours() : d.getHours();
    const mm = useUtc ? d.getUTCMinutes() : d.getMinutes();
    return `${y}-${pad(m)}-${pad(day)}T${pad(hh)}:${pad(mm)}`;
  }
  return '';
}

/** datetime-local → "YYYY-MM-DD HH:MM:00" para a API. */
export function fromDateTimeLocal(value: string): string {
  if (!value) return '';
  const [date, time] = value.split('T');
  if (!date || !time) return value;
  const hhmm = time.slice(0, 5);
  return `${date} ${hhmm}:00`;
}

/** Junta data (YYYY-MM-DD ou dd/mm/aaaa) + HH:MM → datetime SQL. */
export function combineDateAndTime(dateValue: string, hhmm: string): string {
  const ymd = dateValue.includes('/') ? brToYmd(dateValue) : toDateInput(dateValue);
  const t = hhmm.length === 5 ? `${hhmm}:00` : hhmm;
  return `${ymd} ${t}`;
}

export function apiErrorMessage(data: unknown, fallback: string): string {
  if (
    data &&
    typeof data === 'object' &&
    'mensagem' in data &&
    typeof (data as { mensagem: unknown }).mensagem === 'string' &&
    (data as { mensagem: string }).mensagem
  ) {
    return (data as { mensagem: string }).mensagem;
  }
  return fallback;
}
