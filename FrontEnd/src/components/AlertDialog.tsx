import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
};

/** Alerta simples: mensagem + OK. */
export function AlertDialog({
  open,
  title,
  message,
  confirmLabel = 'OK',
  onConfirm,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onConfirm()}>
      <DialogContent>
        <DialogHeader>
          {title ? <DialogTitle>{title}</DialogTitle> : null}
          <DialogDescription>{message}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" className="w-full" onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
