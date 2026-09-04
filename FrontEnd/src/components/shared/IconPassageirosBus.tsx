import { cn } from '@/lib/utils';

type Props = {
  className?: string;
};

/** Ícone colorido — passageiros / ônibus (indicador QTD/P). */
export function IconPassageirosBus({ className }: Props) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('h-8 w-8', className)}
      aria-hidden
    >
      <rect x="5" y="20" width="38" height="18" rx="3.5" fill="#F59E0B" />
      <rect x="5" y="20" width="38" height="5" rx="3.5" fill="#D97706" />
      <rect x="9" y="27" width="9" height="7" rx="1.2" fill="#BAE6FD" stroke="#0284C7" strokeWidth="0.8" />
      <rect x="20" y="27" width="9" height="7" rx="1.2" fill="#BAE6FD" stroke="#0284C7" strokeWidth="0.8" />
      <rect x="31" y="27" width="8" height="7" rx="1.2" fill="#BAE6FD" stroke="#0284C7" strokeWidth="0.8" />
      <circle cx="14" cy="40" r="3.2" fill="#1E293B" />
      <circle cx="34" cy="40" r="3.2" fill="#1E293B" />
      <circle cx="14" cy="40" r="1.4" fill="#94A3B8" />
      <circle cx="34" cy="40" r="1.4" fill="#94A3B8" />
      <circle cx="13" cy="13" r="4" fill="#2563EB" />
      <circle cx="24" cy="10.5" r="4.2" fill="#16A34A" />
      <circle cx="35" cy="13" r="4" fill="#DC2626" />
      <path
        d="M11 17c1.2-2.2 3-3.5 5-3.5M37 17c-1.2-2.2-3-3.5-5-3.5"
        stroke="#475569"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path d="M17 17h14" stroke="#475569" strokeWidth="2" strokeLinecap="round" />
      <rect x="38" y="24" width="3" height="4" rx="0.8" fill="#FDE68A" stroke="#CA8A04" strokeWidth="0.6" />
    </svg>
  );
}
