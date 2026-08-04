import logoMapa3d from '@/assets/logo-mapa-3d.png';

/** Logo da Tela 01 — círculo transparente sobre o fundo da tela. */
export function Logo() {
  return (
    <div className="flex w-full flex-col items-center bg-transparent">
      <img
        src={logoMapa3d}
        alt="RedMapa - Mapa"
        width={160}
        height={160}
        className="mx-auto mb-6 h-auto w-40 max-w-[160px] bg-transparent object-contain"
        draggable={false}
      />
    </div>
  );
}
