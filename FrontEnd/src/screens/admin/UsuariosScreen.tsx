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
import {
  createUser,
  deleteUser,
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
import { ScreenLabel } from '@/components/shared/ScreenLabel';
import { FormField } from '@/components/forms/FormField';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { CodigoPerfil, PerfilItem, UsuarioLista } from '@/types';
import {
  isAlphanumericName,
  isNumericMatricula,
  onlyDigits,
} from '@/utils/validation';

/** idle | include | search | edit */
type FormMode = 'idle' | 'include' | 'search' | 'edit';

const MSG_CADASTRO_OK = 'Usuário cadastrado com sucesso!';
const MSG_ATUALIZADO_OK = 'Usuário atualizado com sucesso!';
const MSG_EXCLUIDO_OK = 'Usuário excluído com sucesso!';
const MSG_RESET_OK = 'Reset de usuário realizado com sucesso!';
const MSG_RESET_FAIL = 'Não foi possível realizar o reset da senha!';
const MSG_NAO_ENCONTRADA = 'Matrícula não encontrada';

/** Tela 03 — Cadastro de Usuário (regras de estado) */
export function UsuariosScreen() {
  const navigate = useNavigate();
  const matriculaRef = useRef<HTMLInputElement>(null);

  const [allowed, setAllowed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<FormMode>('idle');

  const [idUsuario, setIdUsuario] = useState<number | null>(null);
  const [matricula, setMatricula] = useState('');
  const [nome, setNome] = useState('');
  const [codigoPerfil, setCodigoPerfil] = useState<CodigoPerfil>(2);
  const [perfis, setPerfis] = useState<PerfilItem[]>([]);

  const [infoMsg, setInfoMsg] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  const showMsg = useCallback((message: string) => {
    setInfoMsg(message);
  }, []);

  const focusMatricula = useCallback(() => {
    window.setTimeout(() => matriculaRef.current?.focus(), 50);
  }, []);

  const goIdle = useCallback(() => {
    setMode('idle');
    setIdUsuario(null);
    setMatricula('');
    setNome('');
    setCodigoPerfil(2);
    focusMatricula();
  }, [focusMatricula]);

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
        if (data.usuario.codigo_perfil !== 1) {
          setInfoMsg('Acesso restrito a Administradores.');
          setAllowed(false);
          return;
        }
        if (!cancelled) {
          setAllowed(true);
          await carregarPerfis();
          focusMatricula();
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
  }, [carregarPerfis, focusMatricula, navigate]);

  // Idle: Matrícula habilitada; Nome/Perfil só em include/edit
  const matriculaEnabled = mode === 'idle' || mode === 'include' || mode === 'search';
  const nomeEnabled = mode === 'include' || mode === 'edit';
  const perfilEnabled = mode === 'include' || mode === 'edit';

  const canNovo = !busy;
  const canPesquisar = !busy;
  const canSalvar = !busy && (mode === 'include' || mode === 'edit');
  const canDeletar = !busy && mode === 'edit' && idUsuario != null;
  const canReset = !busy && mode === 'edit' && idUsuario != null;

  const onNovo = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const lista = await carregarPerfis();
      setIdUsuario(null);
      setMatricula('');
      setNome('');
      const desp = lista.find((p) => Number(p.codigo_perfil) === 2);
      setCodigoPerfil((desp ? Number(desp.codigo_perfil) : 2) as CodigoPerfil);
      setMode('include');
      focusMatricula();
    } catch {
      showMsg('Falha ao carregar perfis.');
    } finally {
      setBusy(false);
    }
  };

  const executarBuscaMatricula = async () => {
    if (busy) return;
    const mat = matricula.trim();
    if (!mat || !isNumericMatricula(mat)) {
      showMsg('Matrícula deve ser exclusivamente numérica.');
      focusMatricula();
      return;
    }

    setBusy(true);
    try {
      await carregarPerfis();
      const { response, data } = await getUserByMatricula(mat);
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const msg =
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : MSG_NAO_ENCONTRADA;
        showMsg(msg);
        setIdUsuario(null);
        setNome('');
        setCodigoPerfil(2);
        setMode('idle');
        focusMatricula();
        return;
      }
      const u = data.usuario as UsuarioLista;
      setIdUsuario(u.id_usuario);
      setMatricula(String(u.matricula));
      setNome(String(u.nome));
      setCodigoPerfil(Number(u.codigo_perfil) as CodigoPerfil);
      // Após Pesquisar com sucesso: Nome, Perfil e Reset habilitados (modo edit)
      setMode('edit');
    } catch {
      showMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  const onPesquisar = () => {
    void executarBuscaMatricula();
  };

  const onMatriculaKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && (mode === 'idle' || mode === 'search')) {
      e.preventDefault();
      void executarBuscaMatricula();
    }
  };

  const onSalvar = async () => {
    if (!canSalvar) return;
    const mat = matricula.trim();
    const nomeTrim = nome.trim();

    if (!mat || !isNumericMatricula(mat)) {
      showMsg('Matrícula deve ser exclusivamente numérica.');
      return;
    }
    if (!isAlphanumericName(nomeTrim)) {
      showMsg('Nome deve ser alfanumérico (letras, números e espaços).');
      return;
    }
    if (!codigoPerfil) {
      showMsg('Selecione um perfil.');
      return;
    }

    setBusy(true);
    try {
      if (mode === 'include') {
        const { response, data } = await createUser(mat, nomeTrim, codigoPerfil);
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
    if (idUsuario == null) return;
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
      <div className="page">
        <PageHeader title="Cadastro de Usuário" onBack={() => navigate(-1)} />
        <div className="flex flex-1 items-center justify-center text-muted-foreground">
          Carregando…
        </div>
      </div>
    );
  }

  if (!allowed) {
    return (
      <div className="page">
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
    <div className="page">
      <PageHeader
        title="Cadastro de Usuário"
        onBack={() => navigate('/configuracao')}
      />

      <div className="page-body">
        <div className="field-stack">
          <FormField
            ref={matriculaRef}
            label="Matrícula"
            requiredMark
            name="matricula"
            type="tel"
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="Digite a matrícula"
            value={matricula}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setMatricula(onlyDigits(e.target.value))
            }
            onKeyDown={onMatriculaKeyDown}
            disabled={!matriculaEnabled}
            enterKeyHint="search"
          />

          <FormField
            label="Nome"
            requiredMark
            name="nome"
            type="text"
            placeholder="Nome do usuário"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            disabled={!nomeEnabled}
          />

          <div className="flex w-full flex-col gap-1.5">
            <Label className="text-[15px] font-semibold">
              Perfil <span className="req">*</span>
            </Label>
            <Select
              value={String(codigoPerfil)}
              onValueChange={(v) => setCodigoPerfil(Number(v) as CodigoPerfil)}
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
        </div>

        <Separator className="bg-foreground/20" />

        <ButtonToolbar actions={actions} />

        <div className="mt-auto flex justify-end pt-6">
          <Button
            type="button"
            variant="toolbar"
            size="reset"
            disabled={!canReset}
            onClick={() => {
              if (!canReset) return;
              setConfirmReset(true);
            }}
          >
            <IconReset />
            Reset
          </Button>
        </div>
      </div>

      <ScreenLabel text="Tela 03 — Cadastro de Usuário" />

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
    </div>
  );
}
