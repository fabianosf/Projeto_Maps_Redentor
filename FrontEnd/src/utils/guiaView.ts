/** Helpers de apresentação da Guia — sem consolidação de negócio. */

import type { GuiaRoletaBloco, GuiaViagemCard } from '@/types/guia';

export type StatusOperacionalViagem = 'concluida' | 'em_transito' | 'pendente';

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

/** Status operacional do trecho/viagem na lista compacta. */
export function labelStatusOperacional(status: StatusOperacionalViagem): string {
  switch (status) {
    case 'concluida':
      return 'Concluída';
    case 'em_transito':
      return 'Em trânsito';
    case 'pendente':
      return 'Pendente';
    default:
      return status;
  }
}

export function stripeClassStatusOperacional(
  status: StatusOperacionalViagem,
): string {
  switch (status) {
    case 'concluida':
      return 'bg-emerald-500';
    case 'em_transito':
      return 'bg-sky-500';
    case 'pendente':
      return 'bg-amber-500';
    default:
      return 'bg-slate-400';
  }
}

function _leituraAtiva(bloco?: GuiaRoletaBloco | null): boolean {
  if (!bloco) return false;
  return (
    bloco.status_leitura === 'iniciada' ||
    (bloco.leitura_ini != null && bloco.leitura_fim == null)
  );
}

function _leituraFinalizada(bloco?: GuiaRoletaBloco | null): boolean {
  if (!bloco) return false;
  return (
    bloco.status_leitura === 'finalizada' ||
    (bloco.leitura_ini != null && bloco.leitura_fim != null)
  );
}

/**
 * Deriva Concluída / Em trânsito / Pendente a partir do card consolidado
 * (e opcionalmente do status de trecho, se vier na API).
 */
export function statusOperacionalViagem(
  v: GuiaViagemCard,
): StatusOperacionalViagem {
  const trecho = String(v.trecho_status || '').toUpperCase();
  if (trecho === 'CONCLUIDO') return 'concluida';
  if (trecho === 'EM_TRANSITO') return 'em_transito';
  if (trecho === 'PLANEJADO' || trecho === 'CANCELADO') return 'pendente';

  if (v.status === 'atualizando') return 'em_transito';
  if (_leituraAtiva(v.jae) || _leituraAtiva(v.riocard)) return 'em_transito';

  const temJaE = v.jae != null && (v.jae.leitura_ini != null || v.jae.passageiros != null);
  const temRio =
    v.riocard != null &&
    (v.riocard.leitura_ini != null || v.riocard.passageiros != null);
  if (temJaE || temRio) {
    const jaeOk = !temJaE || _leituraFinalizada(v.jae);
    const rioOk = !temRio || _leituraFinalizada(v.riocard);
    if (jaeOk && rioOk) return 'concluida';
    return 'em_transito';
  }

  if (v.status === 'sincronizado' && v.horario_chegada) return 'concluida';
  return 'pendente';
}

export function contarPendentesOperacionais(viagens: GuiaViagemCard[]): number {
  return viagens.filter((v) => statusOperacionalViagem(v) === 'pendente').length;
}

/** Ação operacional sugerida no card (sem mudar regras de negócio). */
export type ProximaAcaoTipo =
  | 'registrar_saida'
  | 'registrar_chegada'
  | 'revisar_pendencia';

export function labelProximaAcao(tipo: ProximaAcaoTipo): string {
  switch (tipo) {
    case 'registrar_saida':
      return 'Registrar saída';
    case 'registrar_chegada':
      return 'Registrar chegada';
    case 'revisar_pendencia':
      return 'Revisar pendência';
    default:
      return 'Abrir';
  }
}

export function temPendenciaSync(v: GuiaViagemCard): boolean {
  return (
    v.status === 'divergencia' ||
    v.status === 'falha' ||
    v.status === 'manual'
  );
}

/**
 * Prioridade da seção “Próxima ação”:
 * 1) saída (aguardando início)
 * 2) chegada (em trânsito)
 * 3) revisar pendência (divergência/falha/manual)
 */
export function proximaAcaoPreferida(
  viagens: GuiaViagemCard[],
): { viagem: GuiaViagemCard; acao: ProximaAcaoTipo } | null {
  const pendente = viagens.find(
    (v) => statusOperacionalViagem(v) === 'pendente',
  );
  if (pendente) return { viagem: pendente, acao: 'registrar_saida' };

  const emTransito = viagens.find(
    (v) => statusOperacionalViagem(v) === 'em_transito',
  );
  if (emTransito) return { viagem: emTransito, acao: 'registrar_chegada' };

  const revisar = viagens.find((v) => temPendenciaSync(v));
  if (revisar) return { viagem: revisar, acao: 'revisar_pendencia' };

  return null;
}

export type GruposViagensOperacionais = {
  proxima: { viagem: GuiaViagemCard; acao: ProximaAcaoTipo } | null;
  emTransito: GuiaViagemCard[];
  pendentes: GuiaViagemCard[];
  concluidas: GuiaViagemCard[];
};

/** Agrupa para lista operacional (exclui a viagem destacada em “Próxima ação”). */
export function agruparViagensOperacionais(
  viagens: GuiaViagemCard[],
): GruposViagensOperacionais {
  const proxima = proximaAcaoPreferida(viagens);
  const destaqueKey = proxima?.viagem.key;

  const emTransito: GuiaViagemCard[] = [];
  const pendentes: GuiaViagemCard[] = [];
  const concluidas: GuiaViagemCard[] = [];

  for (const v of viagens) {
    if (destaqueKey && v.key === destaqueKey) continue;
    const op = statusOperacionalViagem(v);
    if (op === 'em_transito') emTransito.push(v);
    else if (op === 'pendente') pendentes.push(v);
    else concluidas.push(v);
  }

  return { proxima, emTransito, pendentes, concluidas };
}

/** Indicador compacto Ja E / RioCard (totais separados — nunca soma fontes). */
export function indicadorRoleta(bloco?: GuiaRoletaBloco | null): string {
  if (!bloco) return '—';
  if (bloco.passageiros != null && Number.isFinite(Number(bloco.passageiros))) {
    return String(bloco.passageiros);
  }
  if (bloco.leitura_ini != null && bloco.leitura_fim != null) {
    return String(Number(bloco.leitura_fim) - Number(bloco.leitura_ini));
  }
  if (bloco.leitura_ini != null) return `${bloco.leitura_ini}…`;
  return '—';
}
