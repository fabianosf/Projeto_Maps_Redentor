import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = {
  children: ReactNode;
  className?: string;
};

/** Shell visual da app (coluna max-w-phone). */
export function AppShell({ children, className }: Props) {
  return <div className={cn('app-shell', className)}>{children}</div>;
}
