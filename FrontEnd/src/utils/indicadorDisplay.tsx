import { Clock, Gauge, MapPin, Route, Timer, type LucideIcon } from 'lucide-react';
import { IconIndicadorPassageiros } from '@/components/shared/IconIndicadorPassageiros';
import type { ReactNode } from 'react';

/** Valores fictícios para mockup/documentação (Tela 04 — ainda não operacionais). */
const DEMO_VALUES: Record<number, string> = {
  1: '38',
  2: '78%',
  3: '4m',
  4: '12m',
  5: '186',
};

export type IndicadorTileDemo = {
  cod_ind: number;
  descricao: string;
  detalhe?: string | null;
  id_ind?: number;
};

/** Layout completo de demonstração (documentação), quando nenhum vínculo em tb_ind_perf. */
export const INDICADORES_DEMO_DOCUMENTACAO: IndicadorTileDemo[] = [
  { cod_ind: 1, descricao: 'QTD/P', detalhe: 'Quantidade de passageiros' },
  { cod_ind: 2, descricao: 'OCUP', detalhe: 'Taxa de ocupação' },
  { cod_ind: 3, descricao: 'ATR/M', detalhe: 'Atraso médio' },
  { cod_ind: 99, descricao: 'PONT', detalhe: 'Pontualidade' },
  { cod_ind: 4, descricao: 'INT/V', detalhe: 'Intervalo entre viagens' },
  { cod_ind: 5, descricao: 'KMT/D', detalhe: 'Quilometragem diária' },
];

export function indicadorValorDemonstracao(codInd: number): string {
  if (codInd === 99) return '24';
  return DEMO_VALUES[codInd] ?? '—';
}

export function indicadorLabelDemonstracao(descricao: string, codInd: number): string {
  if (codInd === 1) return 'QTD/P';
  return descricao;
}

/** Ícone visual por cod_ind (catálogo tb_indicador). */
export function indicadorIcon(codInd: number, className?: string): ReactNode {
  const iconClass = className ?? 'h-7 w-7 shrink-0 text-[#1e3a5f]';
  const map: Record<number, ReactNode | LucideIcon> = {
    1: <IconIndicadorPassageiros className="shrink-0" />,
    2: Gauge,
    3: Clock,
    4: Timer,
    5: Route,
    99: MapPin,
  };
  const entry = map[codInd];
  if (entry == null) {
    return <MapPin className={iconClass} strokeWidth={1.75} />;
  }
  if (typeof entry === 'function') {
    const Icon = entry;
    return <Icon className={iconClass} strokeWidth={1.75} />;
  }
  return entry;
}

export function chunkRows<T>(items: T[], size: number): T[][] {
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += size) {
    rows.push(items.slice(i, i + size));
  }
  return rows;
}
