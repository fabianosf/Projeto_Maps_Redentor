/**
 * Frota canônica: C47xxx | C30xxx | D13xxx
 */
import { afterEach, describe, expect, it } from 'vitest';
import {
  configurarRegraFrota,
  erroFrotaDuranteDigitacao,
  normalizarFrotaDigitada,
  placeholderFrotaEmpresa,
  prefixoFrotaEmpresa,
  validarFrota,
  validarFrotaParaEmpresa,
} from '@/utils/frotaVeiculo';

const MSG = /C47xxx/;

describe('frotaVeiculo', () => {
  afterEach(() => {
    configurarRegraFrota(null);
  });

  it('normaliza minúsculas e mantém letra', () => {
    expect(normalizarFrotaDigitada('c47654')).toBe('C47654');
    expect(normalizarFrotaDigitada('d13-450')).toBe('D13450');
    expect(normalizarFrotaDigitada('C30 114')).toBe('C30114');
  });

  it('prefixo por empresa', () => {
    expect(prefixoFrotaEmpresa('Redentor')).toBe('C47');
    expect(prefixoFrotaEmpresa('Futuro')).toBe('C30');
    expect(prefixoFrotaEmpresa('Barra')).toBe('D13');
  });

  it('placeholder por empresa', () => {
    expect(placeholderFrotaEmpresa('Redentor')).toContain('C47');
    expect(placeholderFrotaEmpresa('Futuro')).toContain('C30');
  });

  it('aceita formas canônicas', () => {
    expect(validarFrota('C47654')).toBeNull();
    expect(validarFrota('C30114')).toBeNull();
    expect(validarFrota('D13450')).toBeNull();
    expect(validarFrota('c47654')).toBeNull();
  });

  it('valida compatibilidade com empresa', () => {
    expect(validarFrotaParaEmpresa('C47654', 'Redentor')).toBeNull();
    expect(validarFrotaParaEmpresa('C30114', 'Futuro')).toBeNull();
    expect(validarFrotaParaEmpresa('D13450', 'Barra')).toBeNull();
    expect(validarFrotaParaEmpresa('C47654', 'Futuro')).toMatch(/incompatível|prefixo/i);
  });

  it('rejeita sem letra, tamanho e prefixo inválido', () => {
    expect(validarFrota('47123')).toMatch(MSG);
    expect(validarFrota('C4765')).toMatch(MSG);
    expect(validarFrota('A47123')).toMatch(MSG);
    expect(validarFrota('')).toMatch(MSG);
    expect(validarFrota('X30114')).toMatch(MSG);
  });

  it('erro durante digitação respeita prefixo da empresa', () => {
    expect(erroFrotaDuranteDigitacao('C47', 'Redentor')).toBeNull();
    expect(erroFrotaDuranteDigitacao('C30', 'Redentor')).toMatch(/prefixo/i);
    expect(erroFrotaDuranteDigitacao('C47654', 'Redentor')).toBeNull();
  });
});
