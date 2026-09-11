import { describe, expect, it } from 'vitest';
import {
  forcaSenha,
  labelForcaSenha,
  requisitosSenha,
} from '@/utils/passwordStrength';

describe('passwordStrength', () => {
  it('checklist reflete política', () => {
    const reqs = requisitosSenha('Ab1!');
    expect(reqs.find((r) => r.id === 'min8')?.ok).toBe(false);
    expect(requisitosSenha('Senha@123').every((r) => r.ok)).toBe(true);
  });

  it('força sobe com requisitos', () => {
    expect(forcaSenha('')).toBe(0);
    expect(forcaSenha('abc')).toBe(1);
    expect(forcaSenha('Senha@123')).toBe(4);
    expect(labelForcaSenha(4)).toBe('Forte');
  });
});
