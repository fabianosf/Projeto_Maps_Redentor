import { cn } from '@/lib/utils';

type Props = {
  className?: string;
};

/** Ícone profissional — quantidade de passageiros (QTD/P). */
export function IconIndicadorPassageiros({ className }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-7 w-7', className)}
      aria-hidden
    >
      <circle cx="12" cy="8" r="3.25" stroke="#1e3a5f" strokeWidth="1.75" />
      <path
        d="M5.5 19.5c.6-2.8 2.8-4.5 6.5-4.5s5.9 1.7 6.5 4.5"
        stroke="#1e3a5f"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
      <circle cx="18.5" cy="9" r="2.25" stroke="#334155" strokeWidth="1.5" opacity="0.85" />
      <path
        d="M16.5 17.5c.35-1.65 1.55-2.75 3.5-2.75 1.55 0 2.65.75 3.1 2.25"
        stroke="#334155"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.85"
      />
      <circle cx="5.5" cy="9" r="2.25" stroke="#334155" strokeWidth="1.5" opacity="0.85" />
      <path
        d="M3.5 17.5c.35-1.65 1.55-2.75 3.5-2.75 1.55 0 2.65.75 3.1 2.25"
        stroke="#334155"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.85"
      />
    </svg>
  );
}
