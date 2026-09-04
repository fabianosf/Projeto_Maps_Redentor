import { cn } from '@/lib/utils';

type Props = {
  className?: string;
};

/** Ícone colorido — painel de indicadores (barras + tendência). */
export function IconIndicadoresColorido({ className }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-5 w-5', className)}
      aria-hidden
    >
      <rect x="3" y="4" width="18" height="16" rx="3" fill="#E0F2FE" stroke="#0284C7" strokeWidth="1.2" />
      <rect x="6.5" y="13" width="3" height="5" rx="0.75" fill="#2563EB" />
      <rect x="10.5" y="10" width="3" height="8" rx="0.75" fill="#16A34A" />
      <rect x="14.5" y="7" width="3" height="11" rx="0.75" fill="#EA580C" />
      <path
        d="M7 9.5 L11 8 L14.5 10 L17.5 6.5"
        stroke="#7C3AED"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="17.5" cy="6.5" r="1.2" fill="#7C3AED" />
    </svg>
  );
}
