import logoMapa3d from '@/assets/logo-mapa-3d.png';

/** Logo RedMapa — identidade no topo das telas de autenticação. */
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex w-full flex-col items-center bg-transparent">
      <img
        src={logoMapa3d}
        alt="RedMapa"
        width={compact ? 112 : 144}
        height={compact ? 112 : 144}
        className={
          compact
            ? 'mx-auto mb-2 h-auto w-28 max-w-[112px] bg-transparent object-contain'
            : 'mx-auto mb-3 h-auto w-36 max-w-[144px] bg-transparent object-contain'
        }
        draggable={false}
      />
    </div>
  );
}
