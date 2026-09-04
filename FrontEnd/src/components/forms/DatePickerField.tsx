import { useMemo, useState } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { parseDateBR, toDateBR } from '@/utils/appFormat';

type Props = {
  label?: string;
  value: string;
  onChange: (brDate: string) => void;
  name?: string;
  className?: string;
  inputClassName?: string;
  disabled?: boolean;
  /** Ícone do calendário ao lado do label (2,5 cm à direita), em vez de dentro do input. */
  iconBesideLabel?: boolean;
};

const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];

function parseToDate(br: string): Date | null {
  const ok = parseDateBR(br);
  if (!ok) return null;
  const [d, m, y] = ok.split('/').map(Number);
  return new Date(y, m - 1, d);
}

/** Campo DATA (dd/mm/aaaa) — ícone do DatePicker dentro do input (alinhado à Matrícula). */
export function DatePickerField({
  label = 'DATA',
  value,
  onChange,
  name = 'data',
  className,
  inputClassName,
  iconBesideLabel = false,
  disabled = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const selected = parseToDate(value);

  const [viewYear, setViewYear] = useState(() =>
    selected ? selected.getFullYear() : new Date().getFullYear(),
  );
  const [viewMonth, setViewMonth] = useState(() =>
    selected ? selected.getMonth() : new Date().getMonth(),
  );

  const cells = useMemo(() => {
    const first = new Date(viewYear, viewMonth, 1);
    const startPad = first.getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const out: Array<{ day: number; date: Date } | null> = [];
    for (let i = 0; i < startPad; i++) out.push(null);
    for (let d = 1; d <= daysInMonth; d++) {
      out.push({ day: d, date: new Date(viewYear, viewMonth, d) });
    }
    return out;
  }, [viewMonth, viewYear]);

  const monthLabel = new Date(viewYear, viewMonth, 1).toLocaleDateString('pt-BR', {
    month: 'long',
    year: 'numeric',
  });

  const openPicker = () => {
    if (disabled) return;
    const base = selected ?? new Date();
    setViewYear(base.getFullYear());
    setViewMonth(base.getMonth());
    setOpen(true);
  };

  const pick = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    onChange(toDateBR(`${y}-${m}-${d}`));
    setOpen(false);
  };

  const onTextChange = (raw: string) => {
    const digits = raw.replace(/\D/g, '').slice(0, 8);
    let masked = digits;
    if (digits.length > 4) {
      masked = `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
    } else if (digits.length > 2) {
      masked = `${digits.slice(0, 2)}/${digits.slice(2)}`;
    }
    onChange(masked);
  };

  return (
    <div className={cn('flex w-full flex-col gap-1.5', className)}>
      {iconBesideLabel ? (
        <div className="flex h-5 items-center">
          <Label
            htmlFor={name}
            className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900"
          >
            {label}
          </Label>
          <button
            type="button"
            aria-label="Abrir calendário"
            onClick={openPicker}
            disabled={disabled}
            className="ml-[2.5cm] flex h-5 w-5 shrink-0 items-center justify-center text-primary disabled:opacity-40"
          >
            <CalendarIcon className="h-4 w-4" strokeWidth={2.25} />
          </button>
        </div>
      ) : (
        <Label
          htmlFor={name}
          className="flex h-5 items-center text-[15px] font-semibold uppercase leading-none text-slate-900"
        >
          {label}
        </Label>
      )}

      <div className="relative flex items-center">
        <Input
          id={name}
          name={name}
          inputMode="numeric"
          placeholder="dd/mm/aaaa"
          value={value}
          onChange={(e) => onTextChange(e.target.value)}
          disabled={disabled}
          className={cn(
            'h-12 rounded-lg border-slate-400 bg-white text-base text-slate-900',
            iconBesideLabel ? 'pr-3' : 'pr-11',
            inputClassName,
          )}
        />
        {!iconBesideLabel ? (
          <button
            type="button"
            aria-label="Abrir calendário"
            onClick={openPicker}
            className="absolute right-2 z-[1] flex h-9 w-9 items-center justify-center rounded-md text-primary"
          >
            <CalendarIcon className="h-5 w-5" strokeWidth={2.25} />
          </button>
        ) : null}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-[320px] gap-3 rounded-xl p-4">
          <DialogHeader>
            <DialogTitle className="text-center text-base capitalize">{monthLabel}</DialogTitle>
          </DialogHeader>

          <div className="flex items-center justify-between">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Mês anterior"
              onClick={() => {
                const d = new Date(viewYear, viewMonth - 1, 1);
                setViewYear(d.getFullYear());
                setViewMonth(d.getMonth());
              }}
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Próximo mês"
              onClick={() => {
                const d = new Date(viewYear, viewMonth + 1, 1);
                setViewYear(d.getFullYear());
                setViewMonth(d.getMonth());
              }}
            >
              <ChevronRight className="h-5 w-5" />
            </Button>
          </div>

          <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-muted-foreground">
            {WEEKDAYS.map((w, i) => (
              <span key={`${w}-${i}`}>{w}</span>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {cells.map((cell, idx) => {
              if (!cell) return <span key={`e-${idx}`} />;
              const isSelected =
                selected != null &&
                cell.date.getFullYear() === selected.getFullYear() &&
                cell.date.getMonth() === selected.getMonth() &&
                cell.date.getDate() === selected.getDate();
              return (
                <button
                  key={`${cell.date.getFullYear()}-${cell.date.getMonth()}-${cell.day}`}
                  type="button"
                  onClick={() => pick(cell.date)}
                  className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium',
                    isSelected
                      ? 'bg-primary text-primary-foreground'
                      : 'text-slate-900 hover:bg-secondary',
                  )}
                >
                  {cell.day}
                </button>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
