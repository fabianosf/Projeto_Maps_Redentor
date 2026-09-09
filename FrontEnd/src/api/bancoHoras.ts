import { apiFetch } from './client';
import type { ApiSuccess } from '@/types/api';

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
  escalas_encerradas: BancoHorasEscalaEncerrada[];
  escala_em_andamento: BancoHorasEscalaAndamento | null;
  total_minutos_encerrados: number;
  total_encerrado_hhmm: string;
  total_minutos_estimativa_andamento: number;
  total_estimativa_andamento_hhmm: string;
  alertas: string[];
};

export type BancoHorasResponse = ApiSuccess<{ banco_horas: BancoHorasDia }>;

export async function getBancoHorasMotorista(
  idMotorista: number,
  data: string,
): Promise<BancoHorasResponse> {
  const q = new URLSearchParams({ data });
  return apiFetch<BancoHorasResponse>(
    `/motoristas/${idMotorista}/banco-horas?${q.toString()}`,
    { method: 'GET' },
  );
}
