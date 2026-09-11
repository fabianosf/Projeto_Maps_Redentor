import { describe, expect, it } from 'vitest';
import {
  agruparViagensOperacionais,
  contarPendentesOperacionais,
  formatDataChip,
  indicadorRoleta,
  labelProximaAcao,
  labelStatusGuia,
  labelStatusOperacional,
  statusOperacionalViagem,
  stripeClassStatusOperacional,
} from '@/utils/guiaView';
import type { GuiaViagemCard } from '@/types/guia';

function card(partial: Partial<GuiaViagemCard>): GuiaViagemCard {
  return {
    key: 'k',
    viagem_label: 'Viagem 01',
    veiculo: '100',
    data: '11/09/2026',
    sentido: 'ida',
    horario: '07:00',
    embarques: 0,
    origem: 'mapa',
    status: 'pendente',
    ...partial,
  };
}

describe('guiaView', () => {
  it('formatDataChip marca hoje', () => {
    const agora = new Date(2026, 8, 11);
    expect(formatDataChip('11/09/2026', agora)).toMatch(/^Hoje,/);
    expect(formatDataChip('10/09/2026', agora)).toBe('10 set');
  });

  it('labelStatusGuia cobre sync', () => {
    expect(labelStatusGuia('sincronizado')).toBe('Sincronizado');
    expect(labelStatusGuia('pendente')).toBe('Pendente');
    expect(labelStatusGuia('falha')).toBe('Falha');
  });

  it('statusOperacionalViagem prioriza trecho e leituras', () => {
    expect(
      statusOperacionalViagem(card({ trecho_status: 'EM_TRANSITO' })),
    ).toBe('em_transito');
    expect(
      statusOperacionalViagem(card({ trecho_status: 'CONCLUIDO' })),
    ).toBe('concluida');
    expect(
      statusOperacionalViagem(
        card({
          jae: { leitura_ini: 10, leitura_fim: 20, status_leitura: 'finalizada' },
        }),
      ),
    ).toBe('concluida');
    expect(
      statusOperacionalViagem(
        card({
          jae: { leitura_ini: 10, status_leitura: 'iniciada' },
        }),
      ),
    ).toBe('em_transito');
    expect(statusOperacionalViagem(card({ status: 'pendente' }))).toBe('pendente');
  });

  it('labels e stripe operacional', () => {
    expect(labelStatusOperacional('concluida')).toBe('Concluída');
    expect(labelStatusOperacional('em_transito')).toBe('Em trânsito');
    expect(stripeClassStatusOperacional('pendente')).toContain('amber');
  });

  it('contarPendentesOperacionais', () => {
    const n = contarPendentesOperacionais([
      card({ status: 'pendente' }),
      card({
        jae: { leitura_ini: 1, leitura_fim: 2, status_leitura: 'finalizada' },
      }),
    ]);
    expect(n).toBe(1);
  });

  it('indicadorRoleta não soma fontes', () => {
    expect(indicadorRoleta({ passageiros: 12 })).toBe('12');
    expect(indicadorRoleta({ leitura_ini: 100, leitura_fim: 140 })).toBe('40');
    expect(indicadorRoleta(null)).toBe('—');
  });

  it('agrupa próxima ação com prioridade saída > chegada > revisar', () => {
    const grupos = agruparViagensOperacionais([
      card({ key: 'c', trecho_status: 'CONCLUIDO', status: 'sincronizado' }),
      card({ key: 't', trecho_status: 'EM_TRANSITO', status: 'sincronizado' }),
      card({ key: 'p', trecho_status: 'PLANEJADO', status: 'sincronizado' }),
    ]);
    expect(grupos.proxima?.acao).toBe('registrar_saida');
    expect(grupos.proxima?.viagem.key).toBe('p');
    expect(labelProximaAcao('registrar_saida')).toBe('Registrar saída');
    expect(grupos.emTransito.map((v) => v.key)).toEqual(['t']);
    expect(grupos.concluidas.map((v) => v.key)).toEqual(['c']);
  });
});
