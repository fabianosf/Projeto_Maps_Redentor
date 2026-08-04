import type { ReactNode } from 'react';
import { PlusSquare, RotateCcw, Save, Search, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export type ToolbarAction = {
  key: string;
  label: string;
  icon: ReactNode;
  onClick: () => void;
  disabled?: boolean;
};

type Props = {
  actions: ToolbarAction[];
};

/**
 * Barra de 4 botões iguais — Foto das telas/Tela_03.
 * Todos usam `<Button variant="toolbar" size="toolbar" />` do shadcn.
 */
export function ButtonToolbar({ actions }: Props) {
  return (
    <div
      className="grid w-full grid-cols-4 gap-2.5"
      role="toolbar"
      aria-label="Ações do cadastro"
    >
      {actions.map((action) => (
        <Button
          key={action.key}
          type="button"
          variant="toolbar"
          size="toolbar"
          onClick={action.onClick}
          disabled={action.disabled}
        >
          <span aria-hidden="true" className="[&_svg]:h-5 [&_svg]:w-5">
            {action.icon}
          </span>
          <span>{action.label}</span>
        </Button>
      ))}
    </div>
  );
}

export function IconNovo() {
  return <PlusSquare strokeWidth={2.25} />;
}

export function IconSalvar() {
  return <Save strokeWidth={2.25} />;
}

export function IconDeletar() {
  return <Trash2 strokeWidth={2.25} />;
}

export function IconPesquisar() {
  return <Search strokeWidth={2.25} />;
}

export function IconReset() {
  return <RotateCcw strokeWidth={2.25} />;
}
