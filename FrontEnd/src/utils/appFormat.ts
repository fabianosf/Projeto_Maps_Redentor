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
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 10);
  const br = s.match(/^(\d{2})\/(\d{2})\/(\d{4})/);
  if (br) return `${br[3]}-${br[2]}-${br[1]}`;
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
