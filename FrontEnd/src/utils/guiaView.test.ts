import { describe, expect, it } from 'vitest';
import { formatDataChip, labelStatusGuia } from '@/utils/guiaView';

describe('guiaView (apresentação)', () => {
  it('formatDataChip marca hoje', () => {
    const agora = new Date(2026, 8, 10);
    expect(formatDataChip('10/09/2026', agora)).toBe('Hoje, 10 set');
  });

  it('labelStatusGuia cobre status da API', () => {
    expect(labelStatusGuia('sincronizado')).toBe('Sincronizado');
    expect(labelStatusGuia('manual')).toBe('Ajuste manual');
    expect(labelStatusGuia('divergencia')).toBe('Divergência');
  });
});
