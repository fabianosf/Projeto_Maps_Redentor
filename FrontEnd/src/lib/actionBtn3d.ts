/** Botão 3D LightSteelBlue — mesmo estilo do GUIA (Tela 04). */
export const actionBtn3dBase =
  'rounded-lg border border-[#9AABC4]/70 ' +
  'bg-gradient-to-b from-[#C8D6E8] via-[#B0C4DE] to-[#8FA8C9] ' +
  'font-bold uppercase tracking-wide text-slate-900 ' +
  'shadow-[0_6px_14px_rgba(15,23,42,0.22),inset_0_2px_4px_rgba(255,255,255,0.45),inset_0_-4px_7px_rgba(70,90,120,0.25)] ' +
  'transition-transform active:scale-[0.99]';

export const actionBtn3dMd = `h-12 w-full text-base ${actionBtn3dBase}`;

export const actionBtn3dLg =
  `h-14 w-full max-w-[280px] text-[14px] ${actionBtn3dBase}`;

/** Botão toolbar 3D — mesmo estilo do botão Configuração (Tela 04). */
export const toolbarBtn3dBase =
  'h-[39px] min-h-[39px] flex-row gap-1.5 rounded-lg border border-slate-300/90 ' +
  'bg-gradient-to-b from-[#E8EDF3] via-[#D8E0EA] to-[#C5CED9] px-2 text-primary ' +
  'shadow-[0_4px_9px_rgba(15,23,42,0.2),inset_0_2px_3px_rgba(255,255,255,0.55),inset_0_-3px_5px_rgba(100,116,139,0.28)] ' +
  'transition-transform active:scale-[0.98] active:shadow-[0_2px_6px_rgba(15,23,42,0.18),inset_0_2px_6px_rgba(100,116,139,0.32)]';

export const toolbarBtn3d = `${toolbarBtn3dBase} w-[88px] shrink-0 text-[9px] font-bold`;
