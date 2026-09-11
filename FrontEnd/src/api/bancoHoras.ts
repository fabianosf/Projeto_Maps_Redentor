import { apiFetch } from './client';
import type { ApiSuccess } from '@/types/api';

export type BancoHorasViagem = {
  id_viagem: number;
  horario_saida?: string | null;
  horario_chegada?: string | null;
  qtd_pas_ida?: number | null;
  qtd_pas_volta?: number | null;
};

export type BancoHorasEscalaEncerrada = {
  id_item: number;
  idmap: number;
  id_veiculo: number;
  numero_frota?: string;
  inicio_real: string;
  fim_real: string;
  duracao_trabalhada_minutos: number;
  duracao_trabalhada_hhmm: string;
  status_escala: string;
  jornada_prevista_ini?: string | null;
  jornada_prevista_fim?: string | null;
  saldo_diario_minutos?: number | null;
  saldo_diario_hhmm?: string | null;
  situacao?: string;
  empresa?: string | null;
  codigo_linha?: string | number | null;
  linha?: string | null;
  responsavel_registro?: string | null;
  matricula_responsavel?: string | null;
  viagens?: BancoHorasViagem[];
};

export type BancoHorasEscalaAndamento = {
  id_item: number;
  idmap: number;
  id_veiculo: number;
  numero_frota?: string;
  inicio_real: string;
  fim_real: null;
  duracao_estimada_minutos: number;
  duracao_estimada_hhmm: string;
  estimativa: true;
  status_escala: string;
  jornada_prevista_ini?: string | null;
  jornada_prevista_fim?: string | null;
  situacao?: string;
  empresa?: string | null;
  codigo_linha?: string | number | null;
  linha?: string | null;
  responsavel_registro?: string | null;
  matricula_responsavel?: string | null;
  viagens?: BancoHorasViagem[];
};

export type BancoHorasDia = {
  controle: string;
  aviso: string;
  motorista: {
    id_motorista: number;
    matricula?: string;
    nome?: string;
  };
  data: string;
  situacao?: string;
  escalas_encerradas: BancoHorasEscalaEncerrada[];
  escala_em_andamento: BancoHorasEscalaAndamento | null;
  total_minutos_encerrados: number;
  total_encerrado_hhmm: string;
  total_minutos_estimativa_andamento: number;
  total_estimativa_andamento_hhmm: string;
  saldo_diario_minutos?: number | null;
  saldo_diario_hhmm?: string | null;
  alertas: string[];
};

export type BancoHorasPeriodo = {
  controle: string;
  aviso: string;
  motorista: BancoHorasDia['motorista'];
  data_ini: string;
  data_fim: string;
  dias: BancoHorasDia[];
};

export type BancoHorasResponse = ApiSuccess<{ banco_horas: BancoHorasDia }>;
export type BancoHorasPeriodoResponse = ApiSuccess<{
  banco_horas_periodo: BancoHorasPeriodo;
}>;

export type BancoHorasFiltros = {
  id_empresa?: number | null;
  id_linha?: number | null;
  situacao?: string | null;
};

export async function getBancoHorasMotorista(
  idMotorista: number,
  data: string,
  filtros?: BancoHorasFiltros,
): Promise<BancoHorasResponse> {
  const q = new URLSearchParams({ data });
  if (filtros?.id_empresa != null) q.set('id_empresa', String(filtros.id_empresa));
  if (filtros?.id_linha != null) q.set('id_linha', String(filtros.id_linha));
  if (filtros?.situacao) q.set('situacao', filtros.situacao);
  return apiFetch<BancoHorasResponse>(
    `/motoristas/${idMotorista}/banco-horas?${q.toString()}`,
    { method: 'GET' },
  );
}

export async function getBancoHorasPeriodo(
  idMotorista: number,
  dataIni: string,
  dataFim: string,
  filtros?: BancoHorasFiltros,
): Promise<BancoHorasPeriodoResponse> {
  const q = new URLSearchParams({
    data_ini: dataIni,
    data_fim: dataFim,
  });
  if (filtros?.id_empresa != null) q.set('id_empresa', String(filtros.id_empresa));
  if (filtros?.id_linha != null) q.set('id_linha', String(filtros.id_linha));
  if (filtros?.situacao) q.set('situacao', filtros.situacao);
  return apiFetch<BancoHorasPeriodoResponse>(
    `/motoristas/${idMotorista}/banco-horas?${q.toString()}`,
    { method: 'GET' },
  );
}
