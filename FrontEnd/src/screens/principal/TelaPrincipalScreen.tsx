import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bus, Cog, Map } from 'lucide-react';
import { IconIndicadoresColorido } from '@/components/shared/IconIndicadoresColorido';
import { logout, me } from '@/api/auth';
import { getIndicadoresPermitidosMe } from '@/api/indicadoresConfig';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dLg, toolbarBtn3d, toolbarBtn3dBase } from '@/lib/actionBtn3d';
import type { UsuarioPublico } from '@/types';
import type { IndicadorPermitidoItem } from '@/types/indicadores';
import { canAccessConfiguracao } from '@/utils/perfilAccess';
import {
  chunkRows,
  INDICADORES_DEMO_DOCUMENTACAO,
  indicadorIcon,
  indicadorLabelDemonstracao,
  indicadorValorDemonstracao,
  type IndicadorTileDemo,
} from '@/utils/indicadorDisplay';

const BG = '#B0C4DE';

const indicadoresBandBtn3d =
  `${toolbarBtn3dBase} mx-auto w-[calc(100%-3mm)] shrink-0 text-[11px] font-normal`;

const qtdBtn3d =
  'rounded-xl border border-green-200/80 bg-gradient-to-b from-[#F0FDF4] via-[#DCFCE7] to-[#BBF7D0] ' +
  'shadow-[0_5px_11px_rgba(15,23,42,0.2),inset_0_2px_4px_rgba(255,255,255,0.85),inset_0_-4px_7px_rgba(34,197,94,0.15)] ' +
  'transition-transform active:scale-[0.98] active:shadow-[0_3px_8px_rgba(15,23,42,0.18),inset_0_3px_7px_rgba(34,197,94,0.22)]';

const mainActionBtn3d = actionBtn3dLg;

const sectionDividerClass = 'mx-[1.5mm] shrink-0 border-t-2 border-black';

type IndicadorTileProps = {
  label: string;
  value: string;
  icon: ReactNode;
  ariaLabel?: string;
};

function IndicadorTile({ label, value, icon, ariaLabel }: IndicadorTileProps) {
  return (
    <div className="flex w-[72px] flex-col items-center gap-1">
      <span className="text-center text-[11px] font-bold uppercase leading-tight tracking-wide text-slate-800">
        {label}
      </span>
      <div
        aria-label={ariaLabel ?? label}
        className={`flex h-[72px] w-[72px] cursor-default flex-col items-center justify-center text-primary ${qtdBtn3d}`}
      >
        {icon}
        <span className="mt-1 text-[14px] font-bold tabular-nums text-slate-900">{value}</span>
      </div>
    </div>
  );
}

/** Tela 04 — Principal (RN-08: tiles por tb_ind_perf; valores fictícios para documentação). */
export function TelaPrincipalScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);

  const handleVoltar = useCallback(async () => {
    await logout().catch(() => undefined);
    navigate('/', { replace: true });
  }, [navigate]);

  const [usuario, setUsuario] = useState<UsuarioPublico | null>(null);
  const [indicadoresPermitidos, setIndicadoresPermitidos] = useState<IndicadorPermitidoItem[]>(
    [],
  );
  const [loadingInd, setLoadingInd] = useState(true);

  const carregarSessao = useCallback(async () => {
    setLoadingInd(true);
    try {
      const [meRes, indRes] = await Promise.all([me(), getIndicadoresPermitidosMe()]);
      if (meRes.response.ok && meRes.data && 'usuario' in meRes.data) {
        setUsuario(meRes.data.usuario);
      } else {
        setUsuario(null);
        navigate('/', { replace: true });
        return;
      }
      if (indRes.response.ok && indRes.data && 'ok' in indRes.data && indRes.data.ok === true) {
        setIndicadoresPermitidos(indRes.data.indicadores ?? []);
      } else {
        setIndicadoresPermitidos([]);
      }
    } catch {
      setIndicadoresPermitidos([]);
    } finally {
      setLoadingInd(false);
    }
  }, [navigate]);

  useEffect(() => {
    void carregarSessao();
  }, [carregarSessao]);

  const podeConfiguracao = canAccessConfiguracao(usuario?.codigo_perfil);

  const tilesExibir: IndicadorTileDemo[] =
    indicadoresPermitidos.length > 0
      ? indicadoresPermitidos.map((ind) => ({
          id_ind: ind.id_ind,
          cod_ind: ind.cod_ind,
          descricao: ind.descricao,
          detalhe: ind.detalhe,
        }))
      : INDICADORES_DEMO_DOCUMENTACAO;

  const linhasIndicadores = chunkRows(tilesExibir, 4);

  return (
    <div className="page box-border h-dvh max-h-dvh overflow-hidden border border-slate-400 bg-[#B0C4DE] text-slate-900">
      <PageHeader title="RedMapa" onBack={() => void handleVoltar()} />

      <div className="flex min-h-0 flex-1 flex-col bg-[#B0C4DE]">
        <div className="flex shrink-0 items-center justify-end gap-2.5 pb-3 pt-3 pl-4 pr-[calc(1rem-2mm)]">
          {podeConfiguracao ? (
            <Button
              type="button"
              variant="outline"
              aria-label="Configuração"
              onClick={() => navigate('/configuracao')}
              className={toolbarBtn3d}
            >
              <Cog className="h-4 w-4 shrink-0" strokeWidth={2.25} />
              <span className="normal-case leading-tight">Configuração</span>
            </Button>
          ) : null}
          <Button
            type="button"
            variant="outline"
            aria-label="Oficina"
            className={toolbarBtn3d}
            onClick={() => navigate('/mensagem')}
          >
            <Bus className="h-4 w-4 shrink-0" strokeWidth={2.25} />
            <span className="normal-case leading-tight">Oficina</span>
          </Button>
        </div>

        <div className={sectionDividerClass} />

        <div className="min-h-0 flex-1 py-5">
          <div className="mb-4 w-full">
            <Button
              type="button"
              variant="outline"
              aria-label="Indicadores"
              className={indicadoresBandBtn3d}
            >
              <IconIndicadoresColorido className="h-5 w-5 shrink-0" />
              <span
                className="font-normal normal-case tracking-[0.06em] text-black"
                style={{
                  fontFamily: "'Georgia', 'Palatino Linotype', 'Book Antiqua', serif",
                  fontSize: '17px',
                }}
              >
                Indicadores
              </span>
            </Button>
          </div>

          <div className="flex flex-col gap-4 px-3">
            {loadingInd ? (
              <p className="text-center text-sm text-slate-700">Carregando indicadores…</p>
            ) : (
              linhasIndicadores.map((linha) => (
                <div
                  key={linha.map((i) => i.id_ind ?? i.cod_ind).join('-')}
                  className="flex flex-nowrap items-start gap-3"
                >
                  {linha.map((ind) => (
                    <IndicadorTile
                      key={ind.id_ind ?? ind.cod_ind}
                      label={indicadorLabelDemonstracao(ind.descricao, ind.cod_ind)}
                      value={indicadorValorDemonstracao(ind.cod_ind)}
                      icon={indicadorIcon(ind.cod_ind)}
                      ariaLabel={ind.detalhe?.trim() || ind.descricao}
                    />
                  ))}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="mt-auto flex shrink-0 flex-col items-center pb-[calc(2rem-3mm)] pt-4">
          <div className={`${sectionDividerClass} mt-[2mm] mb-[1cm] w-full`} />
          <div className="flex w-full flex-col items-center gap-3 px-6">
            <Button type="button" className={mainActionBtn3d} onClick={() => navigate('/guia')}>
              GUIA
            </Button>
            <Button
              type="button"
              className={`${mainActionBtn3d} gap-2`}
              onClick={() => navigate('/entrada-saida')}
            >
              <Map className="h-5 w-5 shrink-0" strokeWidth={2.25} />
              Chegada | Saída
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
