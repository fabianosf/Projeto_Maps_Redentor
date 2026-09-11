import { MAIN_TABS, type MainTabId } from '@/navigation/mainTabs';
import { cn } from '@/lib/utils';

type Props = {
  activeTab: MainTabId;
  onSelect: (tabId: MainTabId) => void;
};

/**
 * Barra fixa inferior — 5 abas com ícone + rótulo.
 * Safe-area em dispositivos com home indicator.
 */
export function BottomTabBar({ activeTab, onSelect }: Props) {
  return (
    <nav
      className="fixed bottom-0 left-1/2 z-40 flex w-full max-w-phone -translate-x-1/2 border-t border-border/80 bg-card/95 px-0.5 pt-1 shadow-[0_-4px_16px_rgba(15,23,42,0.06)] backdrop-blur-md pb-[max(0.35rem,env(safe-area-inset-bottom))]"
      aria-label="Navegação principal"
    >
      {MAIN_TABS.map((item) => {
        const Icon = item.icon;
        const active = item.id === activeTab;
        return (
          <button
            key={item.id}
            type="button"
            className={cn(
              'flex min-h-[3.15rem] flex-1 flex-col items-center justify-center gap-0.5 px-0.5 text-[10px] font-semibold tracking-wide transition-colors',
              active ? 'text-primary' : 'text-muted-foreground',
            )}
            aria-current={active ? 'page' : undefined}
            aria-label={item.label}
            onClick={() => onSelect(item.id)}
          >
            <span
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full transition-colors',
                active
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-transparent text-muted-foreground',
              )}
            >
              <Icon className="h-4 w-4" strokeWidth={active ? 2.4 : 2} aria-hidden />
            </span>
            <span className="leading-none">{item.label}</span>
            <span
              className={cn(
                'mt-0.5 h-0.5 w-7 rounded-full',
                active ? 'bg-primary' : 'bg-transparent',
              )}
              aria-hidden
            />
          </button>
        );
      })}
    </nav>
  );
}
