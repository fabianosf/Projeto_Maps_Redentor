import { useCallback, useEffect, useState } from 'react';
import { me } from '../api/auth';
import type { UsuarioPublico } from '../types';

export function useAuth() {
  const [usuario, setUsuario] = useState<UsuarioPublico | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const { response, data } = await me();
      if (response.ok && data && 'usuario' in data) {
        setUsuario(data.usuario);
      } else {
        setUsuario(null);
      }
    } catch {
      setUsuario(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { usuario, loading, refresh, setUsuario };
}
