import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { enviarMensagem, listTiposAvaria, type TipoAvaria } from '@/api/mensagem';
import { PageHeader } from '@/components/shared/PageHeader';
import { AppDialog } from '@/components/shared/AppDialog';
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
import { useScreenBg } from '@/hooks/useScreenBg';
import { actionBtn3dMd } from '@/lib/actionBtn3d';
import { cn } from '@/lib/utils';
import { onlyDigits } from '@/utils/validation';
import { SCREEN_BG } from '@/theme/tokens';

const BG = SCREEN_BG;

const screenTextClass = 'text-[15px] font-bold text-slate-900';

const compactFieldHeightClass = 'h-10';

const labelClass =
  'flex h-5 items-center text-[15px] font-semibold leading-none text-slate-900';

const fieldBorderClass = 'rounded-lg border border-black bg-white';

const textoFieldClass =
  'text-justify [text-align-last:left] [text-justify:inter-word] [word-spacing:normal] [hyphens:auto]';

/** Tela Mensagem — registro de avaria (Oficina). */
export function MensagemScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);

  const [tipos, setTipos] = useState<TipoAvaria[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [carro, setCarro] = useState('');
  const [idTip, setIdTip] = useState('');
  const [texto, setTexto] = useState('');
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  const voltar = () => {
    if (window.history.length > 1) {
      navigate(-1);
      return;
    }
    navigate('/principal');
  };

  const carregarTipos = useCallback(async () => {
    setLoading(true);
    try {
      const { response, data } = await listTiposAvaria();
      if (response.ok && data && 'ok' in data && data.ok === true) {
        setTipos(data.tipos ?? []);
        if (data.tipos?.length === 1) {
          setIdTip(String(data.tipos[0].id_tip));
        }
      } else {
        setTipos([]);
      }
    } catch {
      setTipos([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void carregarTipos();
  }, [carregarTipos]);

  const enviar = async () => {
    if (busy) return;
    const numero = carro.trim();
    if (!numero) {
      setInfoMsg('Informe o número do carro.');
      return;
    }
    if (!idTip) {
      setInfoMsg('Selecione o tipo de avaria.');
      return;
    }
    if (!texto.trim()) {
      setInfoMsg('Informe o texto da mensagem.');
      return;
    }

    setBusy(true);
    try {
      const { response, data } = await enviarMensagem({
        numero_frota: numero,
        id_tip: Number(idTip),
        texto: texto.trim(),
      });
      if (!response.ok || !data || !('ok' in data) || data.ok !== true) {
        const msg =
          data && 'mensagem' in data && data.mensagem
            ? data.mensagem
            : 'Não foi possível enviar a mensagem.';
        setInfoMsg(msg);
        return;
      }
      voltar();
    } catch {
      setInfoMsg('Falha de comunicação com a API.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[100dvh] flex-col bg-screen">
        <PageHeader title="MENSAGEM" />
        <p className="p-6 text-center text-sm font-medium text-foreground">Carregando…</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-[100dvh] flex-col bg-screen">
      <PageHeader title="MENSAGEM" />

      <div className="relative flex-1 px-4 pb-4 pt-3">
        <div className="surface-card p-3">
          <div className="mb-3 flex flex-col gap-3">
            <FormField
              label="Carro:"
              name="carro"
              type="tel"
              inputMode="numeric"
              pattern="[0-9]*"
              placeholder="Nº do carro"
              value={carro}
              onChange={(e) => setCarro(onlyDigits(e.target.value))}
              className={cn(
                'w-1/2',
                compactFieldHeightClass,
                fieldBorderClass,
                screenTextClass,
              )}
            />
            <div className="flex w-full flex-col gap-1.5">
              <Label htmlFor="avaria" className={labelClass}>
                Avaria:
              </Label>
              <Select value={idTip || undefined} onValueChange={setIdTip}>
                <SelectTrigger
                  id="avaria"
                  className={cn(
                    'w-full',
                    compactFieldHeightClass,
                    fieldBorderClass,
                    screenTextClass,
                  )}
                >
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  {tipos.map((t) => (
                    <SelectItem key={t.id_tip} value={String(t.id_tip)}>
                      {t.descricao}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="texto" className={labelClass}>
                Texto:
              </Label>
              <textarea
                id="texto"
                name="texto"
                lang="pt-BR"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                className={cn(
                  'h-[7cm] w-full resize-none px-3 py-2',
                  fieldBorderClass,
                  screenTextClass,
                  textoFieldClass,
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                )}
              />
            </div>
          </div>
        </div>

        <div className="absolute inset-x-4 top-[calc(50dvh+3.5cm)]">
          <Separator className="bg-black" />
          <div className="grid grid-cols-2 gap-3 pt-3">
            <Button
              type="button"
              className={actionBtn3dMd}
              onClick={() => void enviar()}
              disabled={busy}
            >
              {busy ? 'Enviando…' : 'Enviar'}
            </Button>
            <Button type="button" className={actionBtn3dMd} onClick={voltar} disabled={busy}>
              Cancelar
            </Button>
          </div>
        </div>
      </div>

      <AppDialog
        open={infoMsg !== null}
        message={infoMsg ?? ''}
        confirmLabel="OK"
        onConfirm={() => setInfoMsg(null)}
      />
    </div>
  );
}
