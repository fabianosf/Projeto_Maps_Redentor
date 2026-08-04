import { Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';

type Props = {
  visible: boolean;
  onToggle: () => void;
};

export function PasswordToggle({ visible, onToggle }: Props) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onToggle}
      aria-label={visible ? 'Ocultar senha' : 'Exibir senha'}
      className="text-muted-foreground"
    >
      {visible ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
    </Button>
  );
}
