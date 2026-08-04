import { useNavigate } from 'react-router-dom';
import { UserCog } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { ScreenLabel } from '@/components/shared/ScreenLabel';
import { Button } from '@/components/ui/button';
import { useScreenBg } from '@/hooks/useScreenBg';

const BG = '#B9C8D4';

/** Tela de Configuração — acessos administrativos. */
export function ConfiguracaoScreen() {
  const navigate = useNavigate();
  useScreenBg(BG);

  return (
    <div className="page h-dvh max-h-dvh overflow-hidden bg-[#B9C8D4] text-slate-900">
      <PageHeader title="CONFIGURAÇÃO" onBack={() => navigate('/principal')} />

      <div className="flex min-h-0 flex-1 flex-col items-center gap-4 bg-[#B9C8D4] px-6 py-8">
        <Button
          type="button"
          className="h-14 w-full max-w-[320px] gap-2 text-[15px]"
          onClick={() => navigate('/cadastro-usuario')}
        >
          <UserCog className="h-5 w-5" strokeWidth={2.25} />
          Cadastro de Usuário
        </Button>
      </div>

      <ScreenLabel text="Tela Configuração" />
    </div>
  );
}
