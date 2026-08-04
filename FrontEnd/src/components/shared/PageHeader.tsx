import type { ReactNode } from 'react';
import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

type Props = {
  title: string;
  onBack?: () => void;
  rightSlot?: ReactNode;
};

export function PageHeader({ title, onBack, rightSlot }: Props) {
  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-1 bg-primary px-2 text-primary-foreground shadow-sm">
      {onBack ? (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Voltar"
          onClick={onBack}
          className="rounded-md border border-primary-foreground/25 text-primary-foreground hover:bg-primary-foreground/10"
        >
          <ChevronLeft className="h-6 w-6" strokeWidth={2.5} />
        </Button>
      ) : (
        <span className="w-11" />
      )}
      <h1 className="flex-1 truncate text-center text-[17px] font-bold uppercase tracking-wide">
        {title}
      </h1>
      <div className="flex h-11 min-w-11 shrink-0 items-center justify-end">
        {rightSlot ?? null}
      </div>
    </header>
  );
}
