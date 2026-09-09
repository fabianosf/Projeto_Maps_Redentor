import { describe, expect, it } from 'vitest';
import {
  erroFrotaDuranteDigitacao,
  mascaraGuiaFrotaEmpresa,
  normalizarFrotaDigitada,
  placeholderFrotaEmpresa,
  prefixoFrotaEmpresa,
  validarFrotaParaEmpresa,
} from '@/utils/frotaVeiculo';

describe('frotaVeiculo', () => {
  it('normaliza para maiúsculas e limita a 6 caracteres', () => {
    expect(normalizarFrotaDigitada('c3011')).toBe('C3011');
    expect(normalizarFrotaDigitada('c30114x')).toBe('C30114');
  });

  it('prefixo fixo por empresa', () => {
    expect(prefixoFrotaEmpresa('Redentor')).toBe('C47');
    expect(prefixoFrotaEmpresa('Futuro')).toBe('C30');
    expect(prefixoFrotaEmpresa('Barra')).toBe('D13');
  });

  it('placeholders e máscaras-guia', () => {
    expect(placeholderFrotaEmpresa('Redentor')).toBe('Ex.: C47654');
    expect(placeholderFrotaEmpresa('Futuro')).toBe('Ex.: C30114');
    expect(placeholderFrotaEmpresa('Barra')).toBe('Ex.: D13450');
    expect(mascaraGuiaFrotaEmpresa('Redentor')).toBe('C47___');
    expect(mascaraGuiaFrotaEmpresa('Futuro')).toBe('C30___');
    expect(mascaraGuiaFrotaEmpresa('Barra')).toBe('D13___');
  });

  it('C47654 aceito somente para Redentor', () => {
    expect(validarFrotaParaEmpresa('C47654', 'Redentor')).toBeNull();
    expect(validarFrotaParaEmpresa('C47654', 'Futuro')).toMatch(/C30/);
    expect(validarFrotaParaEmpresa('C47654', 'Barra')).toMatch(/D13/);
  });

  it('C30114 aceito somente para Futuro', () => {
    expect(validarFrotaParaEmpresa('C30114', 'Futuro')).toBeNull();
    expect(validarFrotaParaEmpresa('C30114', 'Redentor')).toMatch(/C47/);
    expect(validarFrotaParaEmpresa('C30114', 'Barra')).toMatch(/D13/);
  });

  it('D13450 aceito somente para Barra', () => {
    expect(validarFrotaParaEmpresa('D13450', 'Barra')).toBeNull();
    expect(validarFrotaParaEmpresa('D13450', 'Futuro')).toMatch(/C30/);
    expect(validarFrotaParaEmpresa('D13450', 'Redentor')).toMatch(/C47/);
  });

  it('C30450 rejeitado para Barra (é padrão Futuro)', () => {
    expect(validarFrotaParaEmpresa('C30450', 'Barra')).toMatch(/D13/);
    expect(validarFrotaParaEmpresa('C30450', 'Futuro')).toBeNull();
    expect(validarFrotaParaEmpresa('C30450', 'Redentor')).toMatch(/C47/);
  });

  it('rejeita prefixos genéricos fora do padrão', () => {
    expect(validarFrotaParaEmpresa('C12345', 'Futuro')).toMatch(/C30/);
    expect(validarFrotaParaEmpresa('D12345', 'Barra')).toMatch(/D13/);
    expect(validarFrotaParaEmpresa('C47544', 'Futuro')).toMatch(/C30/);
    expect(validarFrotaParaEmpresa('C40000', 'Redentor')).toMatch(/C47/);
  });

  it('mensagens específicas por empresa', () => {
    expect(validarFrotaParaEmpresa('', 'Redentor')).toBe(
      'Informe no formato C47 + 3 números. Ex.: C47654.',
    );
    expect(validarFrotaParaEmpresa('X', 'Futuro')).toBe(
      'Informe no formato C30 + 3 números. Ex.: C30114.',
    );
    expect(validarFrotaParaEmpresa('C30', 'Barra')).toBe(
      'Informe no formato D13 + 3 números. Ex.: D13450.',
    );
  });

  it('durante digitação: parcial compatível sem erro; incompatível com erro', () => {
    expect(erroFrotaDuranteDigitacao('', 'Futuro')).toBeNull();
    expect(erroFrotaDuranteDigitacao('C', 'Futuro')).toBeNull();
    expect(erroFrotaDuranteDigitacao('C30', 'Futuro')).toBeNull();
    expect(erroFrotaDuranteDigitacao('C301', 'Futuro')).toBeNull();
    expect(erroFrotaDuranteDigitacao('D', 'Futuro')).toMatch(/C30/);
    expect(erroFrotaDuranteDigitacao('C47', 'Futuro')).toMatch(/C30/);
    expect(erroFrotaDuranteDigitacao('C30114', 'Futuro')).toBeNull();
    expect(erroFrotaDuranteDigitacao('C47654', 'Futuro')).toMatch(/C30/);
  });
});
