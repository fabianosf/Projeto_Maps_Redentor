import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { getCadastros } from '@/api/cadastros';
import { ApiRequestError } from '@/api/client';
import {
  createUser,
  deleteUser,
  getErpFuncionario,
  getUserByMatricula,
  listPerfis,
  resetUserPassword,
  updateUserProfile,
} from '@/api/users';
import { AlertDialog } from '@/components/AlertDialog';
import { AppShell } from '@/components/AppShell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { FormField } from '@/components/FormField';
import { LoadingState } from '@/components/LoadingState';
import { PageHeader } from '@/components/PageHeader';
import {
  ButtonToolbar,
  IconDeletar,
  IconNovo,
  IconPesquisar,
  IconReset,
  IconSalvar,
} from '@/components/shared/ButtonToolbar';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { useScreenBg } from '@/hooks/useScreenBg';
import type { CodigoPerfil, PerfilItem, UsuarioLista } from '@/types';
import type {
  CadastrosMestres,
  EmpresaCadastro,
  LocalCadastro,
  TurnoCadastro,
} from '@/types/cadastro';
import {
  canAccessCadastroUsuario,
  canResetSenhaUsuario,
  PERFIL_DESPACHANTE,
} from '@/utils/perfilAccess';
import {
  isAlphanumericName,
  isValidMatricula,
  MATRICULA_MAX_LENGTH,
  NOME_MAX_LENGTH,
  onlyMatriculaDigits,
} from '@/utils/validation';

/** idle | include | edit */
type FormMode = 'idle' | 'include' | 'edit';

const MSG_CADASTRO_OK = 'Usuário cadastrado com sucesso!';
const MSG_REATIVADO_OK = 'Usuario reativado com sucesso';
const MSG_ATUALIZADO_OK = 'Usuário atualizado com sucesso!';
const MSG_EXCLUIDO_OK = 'Usuário excluído com sucesso!';
const MSG_RESET_OK = 'Reset de usuário realizado com sucesso!';
const MSG_RESET_FAIL = 'Não foi possível realizar o reset da senha!';
const MSG_MATRICULA_INVALIDA =
  'Matrícula deve ser numérica com no máximo 5 dígitos.';
const MSG_NAO_ENCONTRADA = 'Matrícula não encontrada no RH.';
const MSG_JA_CADASTRADO = 'Usuário já cadastrado.';
const MSG_PREFILL_RH =
  'Matrícula localizada no RH. Complete o cadastro e salve.';
const MSG_NOME_INVALIDO =
  'Nome deve ser alfanumérico (letras, números e espaços).';
const MSG_NOME_TAMANHO = `Nome deve ter no máximo ${NOME_MAX_LENGTH} caracteres.`;
const MSG_ERP_INDISPONIVEL =
  'Cadastro corporativo indisponível. Tente novamente.';
const SCREEN_BG = '#b9c8d4';

function buildFotoSrc(info: {
  foto_url?: string | null;
  foto_base64?: string | null;
  foto_mime?: string | null;
}): string | null {
  if (info.foto_url) return info.foto_url;
  if (!info.foto_base64) return null;
  const mime = info.foto_mime || 'image/jpeg';
  return `data:${mime};base64,${info.foto_base64}`;
}

function normalizeMatriculaInput(value: string): string {
  return onlyMatriculaDigits(value.replace(/\s+/g, ''));
}

function FotoPlaceholder() {
  return (
    <svg
      width="148"
      height="112"
      viewBox="0 0 148 112"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="h-full w-full"
    >
      <rect width="148" height="112" fill="#e2e8f0" />
      <circle cx="74" cy="44" r="22" fill="#94a3b8" />
      <ellipse cx="74" cy="98" rx="38" ry="28" fill="#94a3b8" />
    </svg>
  );
}

function apiErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) {
    return err.body.mensagem || fallback;
  }
  return fallback;
}

function isCadastroAtivo(ativo?: number): boolean {
  return ativo == null || Number(ativo) === 1;
}

function parseCodigoPerfil(value: unknown): CodigoPerfil | null {
  const n = Number(value);
  if (!Number.isInteger(n) || n <= 0) return null;
  return n as CodigoPerfil;
}

const SELECT_EMPTY = '__none__';

function selectValueOrEmpty(value: string): string {
  return value && value.trim() ? value : SELECT_EMPTY;
}

function parseIdPositivo(value: string): number | null {
  if (!value || value === SELECT_EMPTY) return null;
  const n = Number(String(value).trim());
  if (!Number.isInteger(n) || n <= 0) return null;
  return n;
}

function empresasAtivas(cad: CadastrosMestres | null): EmpresaCadastro[] {
  return (cad?.empresas ?? []).filter((e) => isCadastroAtivo(e.ativo));
}

function turnosAtivos(cad: CadastrosMestres | null): TurnoCadastro[] {
  return (cad?.turnos ?? []).filter((t) => isCadastroAtivo(t.ativo));
}

function locaisAtivos(cad: CadastrosMestres | null): LocalCadastro[] {
  return (cad?.locais ?? []).filter((l) => isCadastroAtivo(l.ativo));
}

/** Tela 03 — Cadastro de Usuário (regras de estado). */
export function UsuariosScreen() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const matriculaRef = useRef<HTMLInputElement>(null);

  const allowed = canAccessCadastroUsuario(user?.codigo_perfil);
  const podeResetSenha = canResetSenhaUsuario(user?.codigo_perfil);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<FormMode>('idle');

  const [idUsuario, setIdUsuario] = useState<number | null>(null);
  const [matricula, setMatricula] = useState('');
  const [nome, setNome] = useState('');
  const [codigoPerfil, setCodigoPerfil] = useState<CodigoPerfil>(PERFIL_DESPACHANTE);
  const [perfis, setPerfis] = useState<PerfilItem[]>([]);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [idEmpresa, setIdEmpresa] = useState('');
  const [idTurno, setIdTurno] = useState('');
  const [idLocal, setIdLocal] = useState('');
  const [fotoSrc, setFotoSrc] = useState<string | null>(null);
  const [consultaCadastroMsg, setConsultaCadastroMsg] = useState<string | null>(null);
  const [consultaCadastroErro, setConsultaCadastroErro] = useState<string | null>(null);
  const [consultandoCadastro, setConsultandoCadastro] = useState(false);
  const [nomeSomenteLeitura, setNomeSomenteLeitura] = useState(false);

  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [pesquisarOpen, setPesquisarOpen] = useState(false);
  const [pesquisarMatricula, setPesquisarMatricula] = useState('');

  useScreenBg(SCREEN_BG);

  const showMsg = useCallback((message: string) => {
    setInfoMsg(message);
  }, []);

  const focusMatricula = useCallback(() => {
    window.setTimeout(() => matriculaRef.current?.focus(), 50);
  }, []);

  const limparVinculos = useCallback(() => {
    setIdEmpresa('');
    setIdTurno('');
    setIdLocal('');
  }, []);

  const aplicarDefaultsCadastros = useCallback((cad: CadastrosMestres) => {
    const emp = empresasAtivas(cad)[0];
    const tur = turnosAtivos(cad)[0];
    const loc = locaisAtivos(cad)[0];
    setIdEmpresa(emp ? String(emp.id_empresa) : '');
    setIdTurno(tur ? String(tur.id_turno) : '');
    setIdLocal(loc ? String(loc.id_local) : '');
  }, []);

  const goIdle = useCallback(() => {
    setMode('idle');
    setIdUsuario(null);
    setMatricula('');
    setNome('');
    setCodigoPerfil(PERFIL_DESPACHANTE);
    setFotoSrc(null);
    setConsultaCadastroMsg(null);
    setConsultaCadastroErro(null);
    setConsultandoCadastro(false);
    setNomeSomenteLeitura(false);
    if (cadastros) aplicarDefaultsCadastros(cadastros);
    else limparVinculos();
  }, [aplicarDefaultsCadastros, cadastros, limparVinculos]);

  const aplicarVinculosFromUsuario = useCallback((u: UsuarioLista) => {
    setIdEmpresa(u.id_empresa != null && Number(u.id_empresa) > 0 ? String(u.id_empresa) : '');
    setIdTurno(u.id_turno != null && Number(u.id_turno) > 0 ? String(u.id_turno) : '');
    setIdLocal(u.id_local != null && Number(u.id_local) > 0 ? String(u.id_local) : '');
  }, []);

  const sincronizarVinculosPorPerfil = useCallback(
    (
      perfil: CodigoPerfil,
      cad: CadastrosMestres | null,
      usuario?: UsuarioLista | null,
    ) => {
      const codigo = parseCodigoPerfil(perfil);
      if (codigo !== PERFIL_DESPACHANTE) {
        limparVinculos();
        return;
      }
      if (
        usuario &&
        ((usuario.id_empresa != null && Number(usuario.id_empresa) > 0) ||
          (usuario.id_turno != null && Number(usuario.id_turno) > 0) ||
          (usuario.id_local != null && Number(usuario.id_local) > 0))
      ) {
        aplicarVinculosFromUsuario(usuario);
        return;
      }
      if (cad) aplicarDefaultsCadastros(cad);
      else limparVinculos();
    },
    [aplicarDefaultsCadastros, aplicarVinculosFromUsuario, limparVinculos],
  );

  const garantirVinculosDespachante = useCallback(
    (cad: CadastrosMestres | null = cadastros) => {
      if (parseCodigoPerfil(codigoPerfil) !== PERFIL_DESPACHANTE) return;
      const empOk = empresasAtivas(cad).some((e) => String(e.id_empresa) === idEmpresa);
      const turOk = turnosAtivos(cad).some((t) => String(t.id_turno) === idTurno);
      const locOk = locaisAtivos(cad).some((l) => String(l.id_local) === idLocal);
      if (empOk && turOk && locOk) return;
      if (cad) aplicarDefaultsCadastros(cad);
    },
    [aplicarDefaultsCadastros, cadastros, codigoPerfil, idEmpresa, idLocal, idTurno],
  );

  const carregarCadastros = useCallback(async (): Promise<CadastrosMestres | null> => {
    try {
      const data = await getCadastros();
      setCadastros(data.cadastros);
      return data.cadastros;
    } catch {
      return null;
    }
  }, []);

  const carregarPerfis = useCallback(async (): Promise<PerfilItem[]> => {
    try {
      const data = await listPerfis();
      setPerfis(data.perfis);
      return data.perfis;
    } catch {
      return [];
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }
    if (!allowed) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await Promise.all([carregarPerfis(), carregarCadastros()]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [allowed, authLoading, carregarCadastros, carregarPerfis, navigate, user]);

  // Estado inicial: só Novo/Pesquisar; salvar/deletar só após incluir ou pesquisar.
  const matriculaEnabled = mode === 'include';
  const nomeEnabled = mode === 'include' || mode === 'edit';
  const perfilEnabled = mode === 'include' || mode === 'edit';
  const cadastroEnabled = mode === 'include' || mode === 'edit';
  const codigoPerfilNum = parseCodigoPerfil(codigoPerfil);
  const isDespachante = codigoPerfilNum === PERFIL_DESPACHANTE;
  const vinculoEnabled = cadastroEnabled && isDespachante;

  const empresasOptions = empresasAtivas(cadastros);
  const turnosOptions = turnosAtivos(cadastros);
  const locaisOptions = locaisAtivos(cadastros);
  const vinculosDespachanteOk =
    !isDespachante ||
    (parseIdPositivo(idEmpresa) != null &&
      empresasOptions.some((e) => String(e.id_empresa) === idEmpresa) &&
      parseIdPositivo(idTurno) != null &&
      turnosOptions.some((t) => String(t.id_turno) === idTurno) &&
      parseIdPositivo(idLocal) != null &&
      locaisOptions.some((l) => String(l.id_local) === idLocal));

  const canNovo = !busy;
  const canPesquisar = !busy;
  const canSalvar =
    !busy &&
    (mode === 'include' || mode === 'edit') &&
    Boolean(nome.trim()) &&
    vinculosDespachanteOk;
  const canDeletar = !busy && mode === 'edit' && idUsuario != null;
  // Inspetor: reset sempre desabilitado (negócio + UX); backend exige Admin.
  const canReset = !busy && mode === 'edit' && idUsuario != null && podeResetSenha;

  const onNovo = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const [lista, cad] = await Promise.all([carregarPerfis(), carregarCadastros()]);
      setIdUsuario(null);
      setMatricula('');
      setNome('');
      setFotoSrc(null);
      setConsultaCadastroMsg(null);
      setConsultaCadastroErro(null);
      setNomeSomenteLeitura(false);
      const desp = lista.find((p) => Number(p.codigo_perfil) === PERFIL_DESPACHANTE);
      const perfil = parseCodigoPerfil(
        desp ? desp.codigo_perfil : PERFIL_DESPACHANTE,
      ) ?? PERFIL_DESPACHANTE;
      setCodigoPerfil(perfil);
      sincronizarVinculosPorPerfil(perfil, cad);
      setMode('include');
      focusMatricula();
    } catch {
      showMsg('Falha ao carregar perfis.');
    } finally {
      setBusy(false);
    }
  };

  const validarMatriculaErp = async (opts?: { fromBlur?: boolean }) => {
    if (mode !== 'include' || consultandoCadastro) return;
    const mat = normalizeMatriculaInput(matricula);
    if (!mat || !isValidMatricula(mat)) {
      // Blur com matrícula vazia/inválida: não chama ERP nem mostra erro.
      if (opts?.fromBlur) return;
      showMsg(MSG_MATRICULA_INVALIDA);
      focusMatricula();
      return;
    }

    setMatricula(mat);
    setConsultaCadastroErro(null);
    setConsultaCadastroMsg('Consultando cadastro...');
    setConsultandoCadastro(true);
    try {
      const [func, cad] = await Promise.all([
        getErpFuncionario(mat),
        cadastros ? Promise.resolve(cadastros) : carregarCadastros(),
      ]);
      setNome(String(func.nome).slice(0, NOME_MAX_LENGTH));
      setFotoSrc(buildFotoSrc(func));
      setNomeSomenteLeitura(func.origem === 'oracle');
      setConsultaCadastroMsg(
        `${func.matricula} — ${String(func.nome).slice(0, NOME_MAX_LENGTH)} (${func.origem})`,
      );
      // Mantém/reaplica Empresa/Turno/Local após consulta Oracle.
      garantirVinculosDespachante(cad);
    } catch (err) {
      if (
        err instanceof ApiRequestError &&
        err.status === 503 &&
        err.body.codigo === 'erp_indisponivel'
      ) {
        setConsultaCadastroMsg(null);
        setConsultaCadastroErro(MSG_ERP_INDISPONIVEL);
        setFotoSrc(null);
        setNomeSomenteLeitura(false);
        return;
      }
      setConsultaCadastroMsg(null);
      setConsultaCadastroErro(
        'Matrícula não encontrada no cadastro de funcionários. Confira o número informado.',
      );
      setNome('');
      setFotoSrc(null);
      setNomeSomenteLeitura(false);
      focusMatricula();
    } finally {
      setConsultandoCadastro(false);
    }
  };

  const executarBuscaMatricula = async (matriculaInformada?: string) => {
    if (busy) return;
    const mat = normalizeMatriculaInput(matriculaInformada ?? matricula);
    if (!mat || !isValidMatricula(mat)) {
      showMsg(MSG_MATRICULA_INVALIDA);
      return;
    }

    setBusy(true);
    try {
      const [, cad] = await Promise.all([carregarPerfis(), carregarCadastros()]);
      const data = await getUserByMatricula(mat);
      const u = data.usuario;
      const jaCadastrado =
        Boolean(data.ja_cadastrado) &&
        u.id_usuario != null &&
        Number(u.id_usuario) > 0;

      if (jaCadastrado) {
        const perfil =
          parseCodigoPerfil(u.codigo_perfil) ?? PERFIL_DESPACHANTE;
        setIdUsuario(Number(u.id_usuario));
        setMatricula(String(u.matricula));
        setNome(String(u.nome));
        setCodigoPerfil(perfil);
        setFotoSrc(buildFotoSrc(u));
        setConsultaCadastroMsg(null);
        setConsultaCadastroErro(null);
        setNomeSomenteLeitura(false);
        sincronizarVinculosPorPerfil(perfil, cad, {
          id_usuario: Number(u.id_usuario),
          matricula: String(u.matricula),
          nome: String(u.nome),
          ativo: u.ativo ?? 1,
          trocar_senha: 0,
          codigo_perfil: perfil,
          id_empresa: u.id_empresa ?? null,
          id_turno: u.id_turno ?? null,
          id_local: u.id_local ?? null,
        });
        setMode('edit');
        setPesquisarOpen(false);
        setPesquisarMatricula('');
        showMsg(data.mensagem || MSG_JA_CADASTRADO);
        return;
      }

      // Existe no RH, ainda não cadastrado localmente → preenche inclusão.
      const perfil = PERFIL_DESPACHANTE;
      setIdUsuario(null);
      setMatricula(String(u.matricula));
      setNome(String(u.nome ?? '').slice(0, NOME_MAX_LENGTH));
      setCodigoPerfil(perfil);
      setFotoSrc(buildFotoSrc(u));
      setConsultaCadastroMsg(
        `${u.matricula} — ${String(u.nome ?? '').slice(0, NOME_MAX_LENGTH)} (${u.origem ?? 'rh'})`,
      );
      setConsultaCadastroErro(null);
      setNomeSomenteLeitura(String(u.origem ?? '') === 'oracle');
      sincronizarVinculosPorPerfil(perfil, cad);
      setMode('include');
      setPesquisarOpen(false);
      setPesquisarMatricula('');
      showMsg(data.mensagem || MSG_PREFILL_RH);
    } catch (err) {
      showMsg(apiErrorMessage(err, MSG_NAO_ENCONTRADA));
      setIdUsuario(null);
      setNome('');
      setFotoSrc(null);
      setConsultaCadastroMsg(null);
      setConsultaCadastroErro(null);
      setNomeSomenteLeitura(false);
      setCodigoPerfil(PERFIL_DESPACHANTE);
      setMode('idle');
    } finally {
      setBusy(false);
    }
  };

  const onPesquisar = () => {
    if (busy) return;
    setPesquisarMatricula('');
    setPesquisarOpen(true);
  };

  const onMatriculaKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    if (mode === 'include') {
      void validarMatriculaErp();
    }
  };

  const onMatriculaBlur = () => {
    if (mode !== 'include') return;
    void validarMatriculaErp({ fromBlur: true });
  };

  const onSalvar = async () => {
    if (!canSalvar) return;
    const mat = matricula.trim();
    const nomeTrim = nome.trim();
    const perfil = parseCodigoPerfil(codigoPerfil);

    if (!mat || !isValidMatricula(mat)) {
      showMsg(MSG_MATRICULA_INVALIDA);
      return;
    }
    if (!nomeTrim) {
      showMsg('Nome é obrigatório.');
      return;
    }
    if (nomeTrim.length > NOME_MAX_LENGTH) {
      showMsg(MSG_NOME_TAMANHO);
      return;
    }
    if (!isAlphanumericName(nomeTrim)) {
      showMsg(MSG_NOME_INVALIDO);
      return;
    }
    if (
      perfil == null ||
      !perfis.some((p) => Number(p.codigo_perfil) === perfil)
    ) {
      showMsg('Selecione um perfil válido.');
      return;
    }

    let vinculos: {
      id_empresa: number | null;
      id_turno: number | null;
      id_local: number | null;
    } = {
      id_empresa: null,
      id_turno: null,
      id_local: null,
    };

    if (perfil === PERFIL_DESPACHANTE) {
      const idEmp = parseIdPositivo(idEmpresa);
      const idTur = parseIdPositivo(idTurno);
      const idLoc = parseIdPositivo(idLocal);
      if (
        idEmp == null ||
        !empresasOptions.some((e) => Number(e.id_empresa) === idEmp) ||
        idTur == null ||
        !turnosOptions.some((t) => Number(t.id_turno) === idTur) ||
        idLoc == null ||
        !locaisOptions.some((l) => Number(l.id_local) === idLoc)
      ) {
        showMsg('Selecione empresa, turno e local válidos.');
        return;
      }
      vinculos = {
        id_empresa: idEmp,
        id_turno: idTur,
        id_local: idLoc,
      };
    }

    setBusy(true);
    try {
      if (mode === 'include') {
        const data = await createUser(mat, nomeTrim, perfil, vinculos);
        const temp =
          data.usuario.senha_temporaria ?? data.senha_temporaria;
        if (data.reativado) {
          showMsg(
            temp ? `${MSG_REATIVADO_OK}. Senha temporária: ${temp}` : MSG_REATIVADO_OK,
          );
        } else {
          showMsg(
            temp
              ? `${MSG_CADASTRO_OK} Senha temporária: ${temp}`
              : MSG_CADASTRO_OK,
          );
        }
        goIdle();
        return;
      }

      if (mode === 'edit' && idUsuario != null) {
        await updateUserProfile(idUsuario, perfil, nomeTrim, vinculos);
        showMsg(MSG_ATUALIZADO_OK);
        goIdle();
      }
    } catch (err) {
      showMsg(apiErrorMessage(err, 'Falha ao salvar usuário.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmarDeletar = async () => {
    if (idUsuario == null) return;
    setConfirmDelete(false);
    setBusy(true);
    try {
      await deleteUser(idUsuario);
      showMsg(MSG_EXCLUIDO_OK);
      goIdle();
    } catch (err) {
      showMsg(apiErrorMessage(err, 'Falha ao deletar usuário.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmarReset = async () => {
    // Regra de negócio: Inspetor nunca reseta (não só visual).
    if (idUsuario == null || !podeResetSenha) return;
    setConfirmReset(false);
    setBusy(true);
    try {
      const data = await resetUserPassword(idUsuario);
      const temp = data.usuario.senha_temporaria;
      showMsg(
        temp ? `${MSG_RESET_OK} Senha temporária: ${temp}` : MSG_RESET_OK,
      );
      setMode('edit');
    } catch (err) {
      showMsg(apiErrorMessage(err, MSG_RESET_FAIL));
    } finally {
      setBusy(false);
    }
  };

  const actions = [
    {
      key: 'novo',
      label: 'Novo',
      icon: <IconNovo />,
      onClick: () => void onNovo(),
      disabled: !canNovo,
    },
    {
      key: 'salvar',
      label: 'Salvar',
      icon: <IconSalvar />,
      onClick: () => void onSalvar(),
      disabled: !canSalvar,
    },
    {
      key: 'deletar',
      label: 'Deletar',
      icon: <IconDeletar />,
      onClick: () => {
        if (!canDeletar) return;
        setConfirmDelete(true);
      },
      disabled: !canDeletar,
    },
    {
      key: 'pesquisar',
      label: 'Pesquisar',
      icon: <IconPesquisar />,
      onClick: onPesquisar,
      disabled: !canPesquisar,
    },
  ];

  if (authLoading || loading) {
    return (
      <AppShell className="bg-[#b9c8d4]">
        <div className="page bg-[#b9c8d4]">
          <PageHeader title="Cadastro de Usuário" onBack={() => navigate(-1)} />
          <LoadingState />
        </div>
      </AppShell>
    );
  }

  if (!allowed) {
    return (
      <AppShell className="bg-[#b9c8d4]">
        <div className="page bg-[#b9c8d4]">
          <PageHeader
            title="Cadastro de Usuário"
            onBack={() => navigate('/configuracao')}
          />
          <AlertDialog
            open
            message="Acesso restrito a Administradores e Inspetores."
            confirmLabel="OK"
            onConfirm={() => navigate('/configuracao')}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell className="bg-[#b9c8d4]">
      <div className="page bg-[#b9c8d4]">
        <PageHeader
          title="Cadastro de Usuário"
          onBack={() => navigate('/configuracao')}
        />

        <div className="page-body bg-[#b9c8d4]">
          <div className="field-stack">
            <div className="mb-4 flex items-start gap-3">
              <div className="w-[calc(50%-6px)] shrink-0">
                <FormField
                  ref={matriculaRef}
                  label="Matrícula"
                  requiredMark
                  name="matricula"
                  type="tel"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={MATRICULA_MAX_LENGTH}
                  placeholder="Digite a matrícula"
                  value={matricula}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => {
                    setMatricula(normalizeMatriculaInput(e.target.value));
                    setConsultaCadastroMsg(null);
                    setConsultaCadastroErro(null);
                    setNomeSomenteLeitura(false);
                    if (mode === 'include') {
                      setFotoSrc(null);
                    }
                  }}
                  onKeyDown={onMatriculaKeyDown}
                  onBlur={onMatriculaBlur}
                  disabled={!matriculaEnabled}
                  enterKeyHint="done"
                />
              </div>
              <div className="-mt-[1mm] ml-auto flex flex-col items-start gap-1.5">
                <Label className="text-[15px] font-semibold uppercase leading-none text-slate-900">
                  FOTO:
                </Label>
                <div
                  className="flex h-[112px] w-[148px] items-center justify-center overflow-hidden rounded-lg border border-slate-400 bg-white"
                  aria-label="Foto do funcionário"
                >
                  {fotoSrc ? (
                    <img
                      src={fotoSrc}
                      alt="Foto do funcionário"
                      className="h-full w-full object-cover object-top"
                    />
                  ) : (
                    <FotoPlaceholder />
                  )}
                </div>
              </div>
            </div>

            {mode === 'include' && (consultaCadastroMsg || consultaCadastroErro) ? (
              <p
                className={`text-sm ${
                  consultaCadastroErro ? 'text-destructive' : 'text-slate-700'
                }`}
                role={consultaCadastroErro ? 'alert' : 'status'}
              >
                {consultaCadastroErro ?? consultaCadastroMsg}
              </p>
            ) : null}

            <FormField
              label="Nome"
              requiredMark
              name="nome"
              type="text"
              maxLength={NOME_MAX_LENGTH}
              placeholder="Nome do usuário"
              value={nome}
              onChange={(e) => setNome(e.target.value.slice(0, NOME_MAX_LENGTH))}
              disabled={!nomeEnabled}
              readOnly={nomeSomenteLeitura}
            />

            <div className="flex w-full flex-col gap-1.5">
              <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                Perfil <span className="req"> *</span>
              </Label>
              <Select
                value={String(codigoPerfilNum ?? PERFIL_DESPACHANTE)}
                onValueChange={(v) => {
                  const perfil = parseCodigoPerfil(v) ?? PERFIL_DESPACHANTE;
                  setCodigoPerfil(perfil);
                  sincronizarVinculosPorPerfil(perfil, cadastros);
                }}
                disabled={!perfilEnabled}
              >
                <SelectTrigger
                  className="h-12 rounded-lg bg-white text-base"
                  disabled={!perfilEnabled}
                >
                  <SelectValue placeholder="Selecione o perfil" />
                </SelectTrigger>
                <SelectContent>
                  {perfis.map((p) => (
                    <SelectItem key={p.id_perfil} value={String(p.codigo_perfil)}>
                      {p.descricao}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 items-start gap-3">
              <div className="flex w-full flex-col gap-1.5">
                <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                  Empresa{isDespachante ? <span className="req"> *</span> : null}
                </Label>
                <Select
                  value={selectValueOrEmpty(idEmpresa)}
                  onValueChange={(v) => setIdEmpresa(v === SELECT_EMPTY ? '' : v)}
                  disabled={!vinculoEnabled}
                >
                  <SelectTrigger
                    className="h-12 rounded-lg bg-white text-base"
                    disabled={!vinculoEnabled}
                  >
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SELECT_EMPTY} disabled>
                      Selecione
                    </SelectItem>
                    {empresasOptions.map((e) => (
                      <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>
                        {e.descricao}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex w-full flex-col gap-1.5">
                <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                  Turno{isDespachante ? <span className="req"> *</span> : null}
                </Label>
                <Select
                  value={selectValueOrEmpty(idTurno)}
                  onValueChange={(v) => setIdTurno(v === SELECT_EMPTY ? '' : v)}
                  disabled={!vinculoEnabled}
                >
                  <SelectTrigger
                    className="h-12 rounded-lg bg-white text-base"
                    disabled={!vinculoEnabled}
                  >
                    <SelectValue placeholder="Selecione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SELECT_EMPTY} disabled>
                      Selecione
                    </SelectItem>
                    {turnosOptions.map((t) => (
                      <SelectItem key={t.id_turno} value={String(t.id_turno)}>
                        {t.descricao}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex w-full flex-col gap-1.5">
              <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                Local{isDespachante ? <span className="req"> *</span> : null}
              </Label>
              <Select
                value={selectValueOrEmpty(idLocal)}
                onValueChange={(v) => setIdLocal(v === SELECT_EMPTY ? '' : v)}
                disabled={!vinculoEnabled}
              >
                <SelectTrigger
                  className="h-12 rounded-lg bg-white text-base"
                  disabled={!vinculoEnabled}
                >
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SELECT_EMPTY} disabled>
                    Selecione
                  </SelectItem>
                  {locaisOptions.map((l) => (
                    <SelectItem key={l.id_local} value={String(l.id_local)}>
                      {`${l.codigo_local} - ${l.descricao}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator className="bg-black" />

          <ButtonToolbar actions={actions} />

          <div className="mt-2 grid grid-cols-4 gap-2.5">
            <span className="col-span-3" />
            <Button
              type="button"
              variant="toolbar"
              size="toolbar"
              disabled={!canReset}
              onClick={() => {
                if (!canReset) return;
                setConfirmReset(true);
              }}
            >
              <span aria-hidden="true" className="[&_svg]:h-5 [&_svg]:w-5">
                <IconReset />
              </span>
              <span>Reset</span>
            </Button>
          </div>
        </div>

        <AlertDialog
          open={infoMsg !== null}
          message={infoMsg ?? ''}
          confirmLabel="OK"
          onConfirm={() => setInfoMsg(null)}
        />

        <ConfirmDialog
          open={confirmDelete}
          title="Excluir usuário"
          message="Confirma a exclusão lógica deste usuário? (ativo = false; dados preservados)"
          confirmLabel="Deletar"
          cancelLabel="Cancelar"
          onConfirm={() => void confirmarDeletar()}
          onCancel={() => setConfirmDelete(false)}
        />

        <ConfirmDialog
          open={confirmReset}
          title="Resetar senha"
          message="Uma senha temporária segura será gerada e o usuário deverá trocá-la no próximo acesso. Continuar?"
          confirmLabel="Resetar"
          cancelLabel="Cancelar"
          onConfirm={() => void confirmarReset()}
          onCancel={() => setConfirmReset(false)}
        />

        <Dialog open={pesquisarOpen} onOpenChange={setPesquisarOpen}>
          <DialogContent className="max-w-[340px] border-slate-400/50 bg-[#B9C8D4] p-5">
            <DialogHeader>
              <DialogTitle className="text-center text-[16px] uppercase tracking-wide text-slate-900">
                Pesquisar usuário
              </DialogTitle>
            </DialogHeader>
            <div className="mt-2">
              <Label
                htmlFor="pesquisa_matricula_usuario"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Matrícula
              </Label>
              <Input
                id="pesquisa_matricula_usuario"
                inputMode="numeric"
                autoComplete="off"
                value={pesquisarMatricula}
                onChange={(e) =>
                  setPesquisarMatricula(onlyMatriculaDigits(e.target.value))
                }
                maxLength={MATRICULA_MAX_LENGTH}
                className="h-12 rounded-lg border-slate-400 bg-white text-base text-slate-900"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    void executarBuscaMatricula(pesquisarMatricula);
                  }
                }}
              />
            </div>
            <DialogFooter className="mt-5">
              <Button
                type="button"
                className="w-full"
                disabled={busy || !pesquisarMatricula.trim()}
                onClick={() => void executarBuscaMatricula(pesquisarMatricula)}
              >
                OK
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AppShell>
  );
}
