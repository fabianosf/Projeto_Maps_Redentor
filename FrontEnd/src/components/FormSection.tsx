import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  /** id para aria-labelledby */
  id?: string;
};

/** Bloco de formulário/seção com título corporativo consistente. */
export function FormSection({
  title,
  description,
  children,
  className,
  id,
}: Props) {
  const titleId = id ?? `section-${title.toLowerCase().replace(/\s+/g, '-')}`;
  return (
    <section
      className={cn(
        'flex flex-col gap-3 rounded-xl border border-border/70 bg-card/90 p-4 shadow-sm',
        className,
      )}
      aria-labelledby={titleId}
    >
      <header className="space-y-1">
        <h2
          id={titleId}
          className="text-[13px] font-bold uppercase tracking-wide text-primary"
        >
          {title}
        </h2>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </header>
      <div className="field-stack">{children}</div>
    </section>
  );
}
