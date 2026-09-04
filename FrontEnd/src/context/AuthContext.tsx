import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { logout as apiLogout, me } from '@/api/auth';
import { onSessionExpired } from '@/api/client';
import type { AuthSession, Permissao } from '@/types/auth';
import type { CodigoPerfil, UsuarioPublico } from '@/types/usuario';

function permissoesFromPerfil(codigo: CodigoPerfil): readonly Permissao[] {
  const base: Permissao[] = ['principal', 'guia', 'entrada-saida', 'indicadores'];
  if (codigo === 1) {
    return [...base, 'mapas', 'usuarios', 'configuracao', 'reset_senha'];
  }
  if (codigo === 2) {
    return [...base, 'mapas'];
  }
  if (codigo === 3) {
    return [...base, 'usuarios', 'configuracao'];
  }
  return base;
}

export function toAuthSession(usuario: UsuarioPublico): AuthSession {
  return {
    matricula: usuario.matricula,
    nome: usuario.nome,
    codigo_perfil: usuario.codigo_perfil,
    permissoes: permissoesFromPerfil(usuario.codigo_perfil),
  };
}

type AuthContextValue = {
  user: AuthSession | null;
  loading: boolean;
  setSessionFromUsuario: (usuario: UsuarioPublico) => void;
  clearSession: () => void;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
  hasPermissao: (p: Permissao) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<AuthSession | null>(null);
  const [loading, setLoading] = useState(true);

  const clearSession = useCallback(() => {
    setUser(null);
  }, []);

  const setSessionFromUsuario = useCallback((usuario: UsuarioPublico) => {
    setUser(toAuthSession(usuario));
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await me();
      if (data.autenticado && data.usuario) {
        setUser(toAuthSession(data.usuario));
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      /* cookie já pode ter expirado */
    } finally {
      clearSession();
      navigate('/login', { replace: true });
    }
  }, [clearSession, navigate]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    onSessionExpired(() => {
      clearSession();
      navigate('/login', { replace: true });
    });
    return () => onSessionExpired(null);
  }, [clearSession, navigate]);

  const hasPermissao = useCallback(
    (p: Permissao) => (user?.permissoes.includes(p) ?? false),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      setSessionFromUsuario,
      clearSession,
      refresh,
      logout,
      hasPermissao,
    }),
    [user, loading, setSessionFromUsuario, clearSession, refresh, logout, hasPermissao],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return ctx;
}
