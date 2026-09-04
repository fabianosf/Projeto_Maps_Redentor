import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { me } from '@/api/auth';
import { getCadastros } from '@/api/cadastros';
import {
  createUser,
  deleteUser,
  getErpFuncionario,
  getUserByMatricula,
  listPerfis,
  resetUserPassword,
  updateUserProfile,
} from '@/api/users';
import {
  ButtonToolbar,
  IconDeletar,
  IconNovo,
  IconPesquisar,
  IconReset,
  IconSalvar,
} from '@/components/shared/ButtonToolbar';
import { AppAlertDialog } from '@/components/shared/AppAlertDialog';
import { AppDialog } from '@/components/shared/AppDialog';
import { PageHeader } from '@/components/shared/PageHeader';
import { FormField } from '@/components/forms/FormField';
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
import { useScreenBg } from '@/hooks/useScreenBg';
import type { CodigoPerfil, ErpFuncionario, PerfilItem, UsuarioLista } from '@/types';
import type {
  CadastrosMestres,
  EmpresaCadastro,
  LocalCadastro,
  TurnoCadastro,
} from '@/types/cadastros';
import {
  isAlphanumericName,
  isValidMatricula,
  MATRICULA_MAX_LENGTH,
  NOME_MAX_LENGTH,
  onlyMatriculaDigits,
} from '@/utils/validation';
import {
  canAccessCadastroUsuario,
  canResetSenhaUsuario,
} from '@/utils/perfilAccess';

/** idle | include | edit */
type FormMode = 'idle' | 'include' | 'edit';

const MSG_CADASTRO_OK = 'Usuário cadastrado com sucesso!';
const MSG_ATUALIZADO_OK = 'Usuário atualizado com sucesso!';
const MSG_EXCLUIDO_OK = 'Usuário excluído com sucesso!';
const MSG_RESET_OK = 'Reset de usuário realizado com sucesso!';
const MSG_RESET_FAIL = 'Não foi possível realizar o reset da senha!';
const MSG_MATRICULA_INVALIDA =
  'Matrícula deve ser numérica com no máximo 5 dígitos.';
const MSG_NAO_ENCONTRADA = 'Matrícula não encontrada';
const MSG_NOME_INVALIDO =
  'Nome deve ser alfanumérico (letras, números e espaços).';
const MSG_NOME_TAMANHO = `Nome deve ter no máximo ${NOME_MAX_LENGTH} caracteres.`;
const PERFIL_DESPACHANTE: CodigoPerfil = 2;
const SCREEN_BG = '#b9c8d4';

function buildFotoSrc(
  info: Pick<ErpFuncionario | UsuarioLista, 'foto_base64' | 'foto_mime'>,
): string | null {
  if (!info.foto_base64) return null;
  const mime = info.foto_mime || 'image/jpeg';
  return `data:${mime};base64,${info.foto_base64}`;
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

/** Tela 03 — Cadastro de Usuário (regras de estado) */
export function UsuariosScreen() {
  const navigate = useNavigate();
  const matriculaRef = useRef<HTMLInputElement>(null);

  const [allowed, setAllowed] = useState(false);
  const [podeResetSenha, setPodeResetSenha] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<FormMode>('idle');

  const [idUsuario, setIdUsuario] = useState<number | null>(null);
  const [matricula, setMatricula] = useState('');
  const [nome, setNome] = useState('');
  const [codigoPerfil, setCodigoPerfil] = useState<CodigoPerfil>(2);
  const [perfis, setPerfis] = useState<PerfilItem[]>([]);
  const [cadastros, setCadastros] = useState<CadastrosMestres | null>(null);
  const [idEmpresa, setIdEmpresa] = useState('');
  const [idTurno, setIdTurno] = useState('');
  const [idLocal, setIdLocal] = useState('');
  const [fotoSrc, setFotoSrc] = useState<string | null>(null);

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
    const emp = cad.empresas?.[0] as EmpresaCadastro | undefined;
    const tur = cad.turnos?.[0] as TurnoCadastro | undefined;
    const loc = cad.locais?.[0] as LocalCadastro | undefined;
    setIdEmpresa(emp ? String(emp.id_empresa) : '');
    setIdTurno(tur ? String(tur.id_turno) : '');
    setIdLocal(loc ? String(loc.id_local) : '');
  }, []);

  const goIdle = useCallback(() => {
    setMode('idle');
    setIdUsuario(null);
    setMatricula('');
    setNome('');
    setCodigoPerfil(2);
    setFotoSrc(null);
    if (cadastros) aplicarDefaultsCadastros(cadastros);
    else limparVinculos();
  }, [aplicarDefaultsCadastros, cadastros, limparVinculos]);

  const aplicarVinculosFromUsuario = useCallback((u: UsuarioLista) => {
    setIdEmpresa(u.id_empresa != null ? String(u.id_empresa) : '');
    setIdTurno(u.id_turno != null ? String(u.id_turno) : '');
    setIdLocal(u.id_local != null ? String(u.id_local) : '');
  }, []);

  const sincronizarVinculosPorPerfil = useCallback(
    (
      perfil: CodigoPerfil,
      cad: CadastrosMestres | null,
      usuario?: UsuarioLista | null,
    ) => {
      if (perfil !== PERFIL_DESPACHANTE) {
        limparVinculos();
        return;
      }
      if (
        usuario &&
        (usuario.id_empresa != null ||
          usuario.id_turno != null ||
          usuario.id_local != null)
      ) {
        aplicarVinculosFromUsuario(usuario);
        return;
      }
      if (cad) aplicarDefaultsCadastros(cad);
    },
    [aplicarDefaultsCadastros, aplicarVinculosFromUsuario, limparVinculos],
  );

  const carregarCadastros = useCallback(async () => {
    const { response, data } = await getCadastros();
    if (response.ok && data && 'ok' in data && data.ok === true) {
      setCadastros(data.cadastros);
      return data.cadastros;
    }
    return null;
  }, []);

  const carregarPerfis = useCallback(async () => {
    const { response, data } = await listPerfis();
    if (response.ok && data && 'ok' in data && data.ok === true) {
      setPerfis(data.perfis);
      return data.perfis;
    }
    return [] as PerfilItem[];
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { response, data } = await me();
        if (!response.ok || !data || !('usuario' in data)) {
          navigate('/', { replace: true });
          return;
        }
        if (!canAccessCadastroUsuario(data.usuario.codigo_perfil)) {
          setInfoMsg('Acesso restrito a Administradores e Inspetores.');
          setAllowed(false);
          return;
        }
        if (!cancelled) {
          setPodeResetSenha(canResetSenhaUsuario(data.usuario.codigo_perfil));
          setAllowed(true);
          await Promise.all([carregarPerfis(), carregarCadastros()]);
        }
      } catch {
        navigate('/', { replace: true });
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [carregarCadastros, carregarPerfis, focusMatricula, navigate]);

  // RF-17 — idle: somente Novo/Pesquisar; matrícula só em inclusão
  const matriculaEnabled = mode === 'include';
  const nomeEnabled = mode === 'include' || mode === 'edit';
  const perfilEnabled = mode === 'include' || mode === 'edit';
  const cadastroEnabled = mode === 'include' || mode === 'edit';
  const vinculoEnabled =
    cadastroEnabled && codigoPerfil === PERFIL_DESPACHANTE;

  const canNovo = !busy;
  const canPesquisar = !busy;
  const canSalvar = !busy && (mode === 'include' || mode === 'edit');
  const canDeletar = !busy && mode === 'edit' && idUsuario != null;
  const canReset = !busy && mode === 'edit' && podeResetSenha;

  const onNovo = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const [lista, cad] = await Promise.all([carregarPerfis(), carregarCadastros()]);
      setIdUsuario(null);
      setMatricula('');
      setNome('');
      setFotoSrc(null);
      const desp = lista.find((p) => Number(p.codigo_perfil) === 2);
      setCodigoPerfil((desp ? Number(desp.codigo_perfil) : 2) as CodigoPerfil);
      if (cad) aplicarDefaultsCadastros(cad);
      setMode('include');
      focusMatricula();
    } catch {
      showMsg('Falha ao carregar perfis.');
    } finally {
      setBusy(false);
    }
  };

  const validarMatriculaErp = async () => {
    if (busy || mode !== 'include') return;
    const mat = matricula.trim();
    if (!mat || !isValidMatricula(mat)) {
      showMsg(MSG_MATRICULA_INVALIDA);
      focusMatricula();
      return;
    }

    setBusy(true);
    try {
      const { response, data } = await getErpFuncionario(mat);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const msg =
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : MSG_NAO_ENCONTRADA;
        showMsg(msg);
        setNome('');
        setFotoSrc(null);
        focusMatricula();
        return;
      }
      const func = data.funcionario;
      setNome(String(func.nome).slice(0, NOME_MAX_LENGTH));
      setFotoSrc(buildFotoSrc(func));
    } catch {
      showMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const executarBuscaMatricula = async (matriculaInformada?: string) => {
    if (busy) return;
    const mat = (matriculaInformada ?? matricula).trim();
    if (!mat || !isValidMatricula(mat)) {
      showMsg(MSG_MATRICULA_INVALIDA);
      return;
    }

    setBusy(true);
    try {
      const [, cad] = await Promise.all([carregarPerfis(), carregarCadastros()]);
      const { response, data } = await getUserByMatricula(mat);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const msg =
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : MSG_NAO_ENCONTRADA;
        showMsg(msg);
        setIdUsuario(null);
        setNome('');
        setFotoSrc(null);
        setCodigoPerfil(PERFIL_DESPACHANTE);
        if (cad) aplicarDefaultsCadastros(cad);
        else limparVinculos();
        setMode('idle');
        return;
      }
      const u = data.usuario as UsuarioLista;
      const perfil = Number(u.codigo_perfil) as CodigoPerfil;
      setIdUsuario(u.id_usuario);
      setMatricula(String(u.matricula));
      setNome(String(u.nome));
      setCodigoPerfil(perfil);
      setFotoSrc(buildFotoSrc(u));
      sincronizarVinculosPorPerfil(perfil, cad, u);
      setMode('edit');
      setPesquisarOpen(false);
      setPesquisarMatricula('');
    } catch {
      showMsg('Falha de comunicação com a API.');
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
    if (mode === 'include' && matricula.trim()) {
      void validarMatriculaErp();
    }
  };

  const onSalvar = async () => {
    if (!canSalvar) return;
    const mat = matricula.trim();
    const nomeTrim = nome.trim();

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
    if (!codigoPerfil || !perfis.some((p) => Number(p.codigo_perfil) === codigoPerfil)) {
      showMsg('Selecione um perfil válido.');
      return;
    }
    if (codigoPerfil === PERFIL_DESPACHANTE) {
      const empresas = cadastros?.empresas ?? [];
      const turnos = cadastros?.turnos ?? [];
      const locais = cadastros?.locais ?? [];
      if (
        !idEmpresa ||
        !empresas.some((e) => String(e.id_empresa) === idEmpresa) ||
        !idTurno ||
        !turnos.some((t) => String(t.id_turno) === idTurno) ||
        !idLocal ||
        !locais.some((l) => String(l.id_local) === idLocal)
      ) {
        showMsg('Selecione empresa, turno e local válidos.');
        return;
      }
    }

    const vinculos =
      codigoPerfil === PERFIL_DESPACHANTE
        ? {
            id_empresa: Number(idEmpresa),
            id_turno: Number(idTurno),
            id_local: Number(idLocal),
          }
        : {
            id_empresa: null,
            id_turno: null,
            id_local: null,
          };

    setBusy(true);
    try {
      if (mode === 'include') {
        const { response, data } = await createUser(
          mat,
          nomeTrim,
          codigoPerfil,
          vinculos,
        );
        if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
          showMsg(
            data && 'mensagem' in data && data.mensagem
              ? data.mensagem
              : 'Falha ao salvar usuário.',
          );
          return;
        }
        showMsg(MSG_CADASTRO_OK);
        goIdle();
        return;
      }

      if (mode === 'edit' && idUsuario != null) {
        const { response, data } = await updateUserProfile(
          idUsuario,
          codigoPerfil,
          nomeTrim,
          vinculos,
        );
        if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
          showMsg(
            data && 'mensagem' in data && data.mensagem
              ? data.mensagem
              : 'Falha ao atualizar usuário.',
          );
          return;
        }
        showMsg(MSG_ATUALIZADO_OK);
        goIdle();
      }
    } catch {
      showMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const confirmarDeletar = async () => {
    if (idUsuario == null) return;
    setConfirmDelete(false);
    setBusy(true);
    try {
      const { response, data } = await deleteUser(idUsuario);
      if (!response.ok) {
        showMsg(
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : 'Falha ao deletar usuário.',
        );
        return;
      }
      showMsg(MSG_EXCLUIDO_OK);
      goIdle();
    } catch {
      showMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const confirmarReset = async () => {
    if (idUsuario == null || !podeResetSenha) return;
    setConfirmReset(false);
    setBusy(true);
    try {
      const { response, data } = await resetUserPassword(idUsuario);
      if (!response.ok) {
        showMsg(
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : MSG_RESET_FAIL,
        );
        return;
      }
      showMsg(MSG_RESET_OK);
      setMode('edit');
    } catch {
      showMsg(MSG_RESET_FAIL);
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

  if (loading) {
    return (
      <div className="page bg-[#b9c8d4]">
        <PageHeader title="Cadastro de Usuário" onBack={() => navigate(-1)} />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          Carregando…
        </div>
      </div>
    );
  }

  if (!allowed) {
    return (
      <div className="page bg-[#b9c8d4]">
        <PageHeader title="Cadastro de Usuário" onBack={() => navigate('/configuracao')} />
        <AppDialog
          open={infoMsg !== null}
          message={infoMsg ?? ''}
          confirmLabel="OK"
          onConfirm={() => {
            setInfoMsg(null);
            navigate('/configuracao');
          }}
        />
      </div>
    );
  }

  return (
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
                  setMatricula(onlyMatriculaDigits(e.target.value));
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
          />

          <div className="flex w-full flex-col gap-1.5">
            <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
              Perfil <span className="req"> *</span>
            </Label>
            <Select
              value={String(codigoPerfil)}
              onValueChange={(v) => {
                const perfil = Number(v) as CodigoPerfil;
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
                Empresa
              </Label>
              <Select
                value={idEmpresa}
                onValueChange={setIdEmpresa}
                disabled={!vinculoEnabled}
              >
                <SelectTrigger
                  className="h-12 rounded-lg bg-white text-base"
                  disabled={!vinculoEnabled}
                >
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {(cadastros?.empresas ?? []).map((e) => (
                    <SelectItem key={e.id_empresa} value={String(e.id_empresa)}>
                      {e.descricao}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex w-full flex-col gap-1.5">
              <Label className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900">
                Turno
              </Label>
              <Select value={idTurno} onValueChange={setIdTurno} disabled={!vinculoEnabled}>
                <SelectTrigger
                  className="h-12 rounded-lg bg-white text-base"
                  disabled={!vinculoEnabled}
                >
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {(cadastros?.turnos ?? []).map((t) => (
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
              Local
            </Label>
            <Select value={idLocal} onValueChange={setIdLocal} disabled={!vinculoEnabled}>
              <SelectTrigger
                className="h-12 rounded-lg bg-white text-base"
                disabled={!vinculoEnabled}
              >
                <SelectValue placeholder="Selecione" />
              </SelectTrigger>
              <SelectContent>
                {(cadastros?.locais ?? []).map((l) => (
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

      <AppDialog
        open={infoMsg !== null}
        message={infoMsg ?? ''}
        confirmLabel="OK"
        onConfirm={() => setInfoMsg(null)}
      />

      <AppAlertDialog
        open={confirmDelete}
        title="Excluir usuário"
        message="Confirma a exclusão deste usuário?"
        confirmLabel="Deletar"
        cancelLabel="Cancelar"
        onConfirm={() => void confirmarDeletar()}
        onCancel={() => setConfirmDelete(false)}
      />

      <AppAlertDialog
        open={confirmReset}
        title="Resetar senha"
        message="A senha será redefinida para a provisória e o usuário deverá trocá-la no próximo acesso. Continuar?"
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
  );
}
