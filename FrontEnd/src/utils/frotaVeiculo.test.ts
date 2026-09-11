/**
 * Validação de frota: 47xxx | 30xxx | 13xxx (independente da empresa).
 */
import { afterEach, describe, expect, it } from 'vitest';
import {
  configurarRegraFrota,
  erroFrotaDuranteDigitacao,
  mascaraGuiaFrotaEmpresa,
  normalizarFrotaDigitada,
  placeholderFrotaEmpresa,
  prefixoFrotaEmpresa,
  validarFrota,
  validarFrotaParaEmpresa,
} from '@/utils/frotaVeiculo';

const MSG = /47xxx/;

describe('frotaVeiculo', () => {
  afterEach(() => {
    configurarRegraFrota(null);
  });

  it('normaliza só dígitos e limita a 5', () => {
    expect(normalizarFrotaDigitada('47-123')).toBe('47123');
    expect(normalizarFrotaDigitada('47 123x')).toBe('47123');
    expect(normalizarFrotaDigitada('C471234')).toBe('47123');
  });

  it('não amarra prefixo à empresa', () => {
    expect(prefixoFrotaEmpresa('Redentor')).toBeNull();
    expect(prefixoFrotaEmpresa('Futuro')).toBeNull();
    expect(prefixoFrotaEmpresa('Barra')).toBeNull();
  });

  it('placeholder genérico', () => {
    expect(placeholderFrotaEmpresa('Redentor')).toBe('Ex.: 47123');
    expect(placeholderFrotaEmpresa('Futuro')).toBe('Ex.: 47123');
    expect(mascaraGuiaFrotaEmpresa('Barra')).toBeNull();
  });

  it('aceita 47xxx, 30xxx e 13xxx em qualquer empresa', () => {
    expect(validarFrota('47123')).toBeNull();
    expect(validarFrota('30123')).toBeNull();
    expect(validarFrota('13123')).toBeNull();
    expect(validarFrotaParaEmpresa('47123', 'Futuro')).toBeNull();
    expect(validarFrotaParaEmpresa('30123', 'Redentor')).toBeNull();
    expect(validarFrotaParaEmpresa('13123', 'Barra')).toBeNull();
  });

  it('rejeita letras, tamanho, prefixo e especiais', () => {
    expect(validarFrota('C47123')).toMatch(MSG);
    expect(validarFrota('D13123')).toMatch(MSG);
    expect(validarFrota('4712')).toMatch(MSG);
    expect(validarFrota('471234')).toMatch(MSG);
    expect(validarFrota('12123')).toMatch(MSG);
    expect(validarFrota('99123')).toMatch(MSG);
    expect(validarFrota('47-123')).toMatch(MSG);
    expect(validarFrota('47 123')).toMatch(MSG);
    expect(validarFrota('')).toMatch(MSG);
  });

  it('erro durante digitação em prefixo inválido', () => {
    expect(erroFrotaDuranteDigitacao('47')).toBeNull();
    expect(erroFrotaDuranteDigitacao('471')).toBeNull();
    expect(erroFrotaDuranteDigitacao('30')).toBeNull();
    expect(erroFrotaDuranteDigitacao('13')).toBeNull();
    expect(erroFrotaDuranteDigitacao('12')).toMatch(MSG);
    expect(erroFrotaDuranteDigitacao('99')).toMatch(MSG);
    expect(erroFrotaDuranteDigitacao('47123')).toBeNull();
    expect(erroFrotaDuranteDigitacao('12123')).toMatch(MSG);
  });

  it('configurarRegraFrota aplica regra da API', () => {
    configurarRegraFrota({
      regex: '^99[0-9]{3}$',
      max_len: 5,
      exemplo: '99123',
      mensagem: 'Use 99xxx.',
      placeholder: 'Ex.: 99123',
    });
    expect(validarFrota('99123')).toBeNull();
    expect(validarFrota('47123')).toBe('Use 99xxx.');
    expect(placeholderFrotaEmpresa('Redentor')).toBe('Ex.: 99123');
  });
});
