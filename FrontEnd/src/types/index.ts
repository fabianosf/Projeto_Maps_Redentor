/** Barrel de tipos do FrontEnd RedMapa. */

export type {
  ApiError,
  ApiResult,
  ApiSuccess,
} from './api';
export { isApiError, isApiSuccess } from './api';

export type {
  AuthSession,
  ChangePasswordResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MeResponse,
  Permissao,
} from './auth';

export type {
  CodigoPerfil,
  ErpFuncionario,
  ErpFuncionarioResponse,
  PerfilItem,
  PerfisListResponse,
  UserMutationResponse,
  UsersListResponse,
  UsuarioLista,
  UsuarioPublico,
} from './usuario';

export type {
  CadastrosMestres,
  CadastrosResponse,
  EmpresaCadastro,
  LinhaCadastro,
  LocalCadastro,
  MotoristaCadastro,
  TurnoCadastro,
  VeiculoCadastro,
} from './cadastro';

export type { Guia, GuiaDeleteResponse, GuiaResponse } from './guia';

export type {
  EntradaSaidaContextoResponse,
  EntradaSaidaRegistrarRequest,
  EntradaSaidaRegistrarResponse,
  LinhaEntradaSaida,
  LinhasSaidaResponse,
  LocalEntradaSaida,
} from './entradaSaida';

export type {
  Indicador,
  IndicadorPermitido,
  IndicadorPermitidoItem,
  IndicadorVinculo,
  IndicadorVinculoItem,
  IndicadoresCatalogoResponse,
  IndicadoresPermitidosMeResponse,
  IndicadoresSaveResponse,
  IndicadoresVinculoResponse,
  PerfisIndicadoresListResponse,
} from './indicador';

/** @deprecated Use ApiError — mantido para imports legados. */
export type { ApiError as ApiErrorBody } from './api';
