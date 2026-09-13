import { MAIN_TABS, type MainTabId } from '@/navigation/mainTabs';
import { cn } from '@/lib/utils';

type Props = {
  activeTab: MainTabId;
  onSelect: (tabId: MainTabId) => void;
};

/**
 * Barra fixa inferior — ícone + rótulo, alvos ≥48px.
 */
export function BottomTabBar({ activeTab, onSelect }: Props) {
  return (
    <nav
      className="fixed bottom-0 left-1/2 z-40 flex w-full max-w-phone -translate-x-1/2 border-t border-field bg-brand-navy px-0.5 pt-1.5 pb-[max(0.4rem,env(safe-area-inset-bottom))] shadow-[0_-4px_16px_color-mix(in_srgb,var(--brand-navy)_18%,transparent)]"
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
              'flex min-h-[48px] flex-1 flex-col items-center justify-center gap-0.5 px-0.5 text-[11px] font-semibold tracking-wide transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cta',
              active ? 'text-white' : 'text-white/70',
            )}
            aria-current={active ? 'page' : undefined}
            aria-label={item.label}
            onClick={() => onSelect(item.id)}
          >
            <span
              className={cn(
                'flex h-9 w-9 items-center justify-center rounded-xl transition-colors',
                active
                  ? 'bg-brand-cta text-white'
                  : 'bg-transparent text-white/75',
              )}
            >
              <Icon className="h-5 w-5" strokeWidth={active ? 2.4 : 2} aria-hidden />
            </span>
            <span className="leading-none">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
