import type { ReactNode } from 'react';
import { Filter, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export type FilterChipItem = {
  id: string;
  label: string;
  onClear?: () => void;
};

type ChipsProps = {
  chips: FilterChipItem[];
  onOpenFilters?: () => void;
  filterActive?: boolean;
  className?: string;
};

/** Chips de filtro ativo + botão Filtrar. */
export function FilterChipsBar({
  chips,
  onOpenFilters,
  filterActive,
  className,
}: ChipsProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {onOpenFilters ? (
        <button
          type="button"
          onClick={onOpenFilters}
          aria-pressed={filterActive}
          className={cn(
            'inline-flex min-h-9 items-center gap-1.5 rounded-full border px-3 text-xs font-semibold',
            filterActive
              ? 'border-primary/40 bg-primary/10 text-primary'
              : 'border-slate-300 bg-white text-slate-700',
          )}
        >
          <Filter className="h-3.5 w-3.5" aria-hidden />
          Filtrar
        </button>
      ) : null}
      {chips.map((c) => (
        <span
          key={c.id}
          className="inline-flex max-w-full items-center gap-1 rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-800"
        >
          <span className="truncate">{c.label}</span>
          {c.onClear ? (
            <button
              type="button"
              aria-label={`Remover filtro ${c.label}`}
              onClick={c.onClear}
              className="rounded-full p-0.5 text-slate-500 hover:bg-slate-200 hover:text-slate-800"
            >
              <X className="h-3 w-3" aria-hidden />
            </button>
          ) : null}
        </span>
      ))}
    </div>
  );
}

type SheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  children: ReactNode;
  onApply?: () => void;
  onClear?: () => void;
  applyLabel?: string;
  clearLabel?: string;
};

/** Painel inferior de filtros (Dialog ancorado embaixo). */
export function FilterBottomSheet({
  open,
  onOpenChange,
  title = 'Filtrar',
  children,
  onApply,
  onClear,
  applyLabel = 'Aplicar',
  clearLabel = 'Limpar',
}: SheetProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          'fixed bottom-0 left-1/2 top-auto z-[60] flex w-full max-w-phone -translate-x-1/2 translate-y-0 flex-col',
          'max-h-[min(85dvh,560px)] rounded-b-none rounded-t-2xl border-x-0 border-b-0 p-0 shadow-2xl',
          'pb-[max(0.75rem,env(safe-area-inset-bottom))]',
        )}
      >
        <div className="mx-auto mt-2 h-1 w-10 shrink-0 rounded-full bg-slate-300" aria-hidden />
        <DialogHeader className="px-4 pb-2 pt-3">
          <DialogTitle className="text-center text-base font-bold uppercase tracking-wide">
            {title}
          </DialogTitle>
        </DialogHeader>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 pb-3">{children}</div>
        <DialogFooter className="flex flex-row gap-2 border-t border-slate-200 px-4 pt-3 sm:justify-between">
          {onClear ? (
            <Button type="button" variant="outline" className="flex-1" onClick={onClear}>
              {clearLabel}
            </Button>
          ) : null}
          {onApply ? (
            <Button type="button" className="flex-1" onClick={onApply}>
              {applyLabel}
            </Button>
          ) : null}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
