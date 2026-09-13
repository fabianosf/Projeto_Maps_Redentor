import * as React from 'react';
import * as TabsPrimitive from '@radix-ui/react-tabs';
import { cn } from '@/lib/utils';

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      'inline-flex h-11 w-full items-center justify-center rounded-lg bg-white/60 p-1 text-text',
      className,
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      'inline-flex flex-1 items-center justify-center rounded-md px-3 py-2 text-sm font-bold uppercase tracking-wide',
      'text-text transition-all',
      'data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow',
      className,
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

/**
 * Conteúdo de aba: forceMount + hidden/inert (sem aria-hidden no ancestral com foco).
 */
const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, forceMount = true, ...props }, ref) => {
  const localRef = React.useRef<HTMLDivElement | null>(null);

  const setRefs = React.useCallback(
    (node: HTMLDivElement | null) => {
      localRef.current = node;
      if (typeof ref === 'function') ref(node);
      else if (ref) (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
    },
    [ref],
  );

  React.useEffect(() => {
    const el = localRef.current;
    if (!el) return;
    const sync = () => {
      const inactive = el.getAttribute('data-state') === 'inactive';
      if (inactive) {
        el.setAttribute('inert', '');
        el.setAttribute('hidden', '');
        el.removeAttribute('aria-hidden');
      } else {
        el.removeAttribute('inert');
        el.removeAttribute('hidden');
        el.removeAttribute('aria-hidden');
      }
    };
    sync();
    const obs = new MutationObserver(sync);
    obs.observe(el, { attributes: true, attributeFilter: ['data-state', 'aria-hidden'] });
    return () => obs.disconnect();
  }, []);

  return (
    <TabsPrimitive.Content
      ref={setRefs}
      forceMount={forceMount}
      className={cn(
        'mt-3 focus-visible:outline-none data-[state=inactive]:hidden',
        className,
      )}
      {...props}
    />
  );
});
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
