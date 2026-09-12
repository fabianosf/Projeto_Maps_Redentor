/** Ícone de ônibus (frente) — line-art branco, só o desenho (sem texto). */
export function LoginBusIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect
        x="14"
        y="10"
        width="36"
        height="40"
        rx="6"
        stroke="currentColor"
        strokeWidth="2.5"
      />
      <path
        d="M14 20h36"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <rect
        x="20"
        y="24"
        width="24"
        height="14"
        rx="2"
        stroke="currentColor"
        strokeWidth="2.25"
      />
      <circle cx="22" cy="46" r="3" fill="currentColor" />
      <circle cx="42" cy="46" r="3" fill="currentColor" />
      <path
        d="M12 28v8M52 28v8"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path
        d="M26 14h12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}
