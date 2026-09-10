/** Helpers de apresentação da Guia — sem consolidação de negócio. */

export function formatDataChip(dataBR: string, agora = new Date()): string {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(dataBR.trim());
  if (!m) return dataBR;
  const d = Number(m[1]);
  const mo = Number(m[2]);
  const y = Number(m[3]);
  const meses = [
    'jan',
    'fev',
    'mar',
    'abr',
    'mai',
    'jun',
    'jul',
    'ago',
    'set',
    'out',
    'nov',
    'dez',
  ];
  const label = `${d} ${meses[mo - 1] ?? ''}`;
  const hoje =
    agora.getDate() === d &&
    agora.getMonth() + 1 === mo &&
    agora.getFullYear() === y;
  return hoje ? `Hoje, ${label}` : label;
}

export function labelStatusGuia(status: string): string {
  switch (status) {
    case 'sincronizado':
      return 'Sincronizado';
    case 'atualizando':
      return 'Atualizando';
    case 'pendente':
      return 'Pendente';
    case 'divergencia':
      return 'Divergência';
    case 'falha':
      return 'Falha';
    case 'manual':
      return 'Ajuste manual';
    default:
      return status;
  }
}
