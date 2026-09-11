import { describe, expect, it } from 'vitest';
import { resolveMainTab, MAIN_TABS } from '@/navigation/mainTabs';

describe('mainTabs', () => {
  it('resolve aba por pathname', () => {
    expect(resolveMainTab('/principal')).toBe('inicio');
    expect(resolveMainTab('/mapas/33')).toBe('mapas');
    expect(resolveMainTab('/guia/nova')).toBe('guia');
    expect(resolveMainTab('/entrada-saida')).toBe('registros');
    expect(resolveMainTab('/banco-horas')).toBe('registros');
    expect(resolveMainTab('/indicadores')).toBe('registros');
    expect(resolveMainTab('/configuracao/indicadores')).toBe('mais');
    expect(resolveMainTab('/usuarios')).toBe('mais');
    expect(resolveMainTab('/mais')).toBe('mais');
  });

  it('tem cinco abas com rótulos', () => {
    expect(MAIN_TABS).toHaveLength(5);
    expect(MAIN_TABS.map((t) => t.label)).toEqual([
      'Início',
      'Mapas',
      'Guia',
      'Registros',
      'Mais',
    ]);
  });
});
