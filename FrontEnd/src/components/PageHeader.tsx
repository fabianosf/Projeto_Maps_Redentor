import type { ReactNode } from 'react';
import { AppHeader } from '@/components/AppHeader';

type Props = {
  title: string;
  onBack?: () => void;
  rightSlot?: ReactNode;
};

/** Alias legado → AppHeader navy. */
export function PageHeader({ title, onBack, rightSlot }: Props) {
  return <AppHeader title={title} onBack={onBack} rightSlot={rightSlot} />;
}
