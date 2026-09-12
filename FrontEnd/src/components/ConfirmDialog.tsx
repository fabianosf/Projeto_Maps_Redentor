import {
  AlertDialog as RadixAlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

type Props = {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Confirmação com OK / Cancelar. */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'OK',
  cancelLabel = 'Cancelar',
  onConfirm,
  onCancel,
}: Props) {
    return (
    <RadixAlertDialog
      open={open}
      onOpenChange={(v) => {
        // Só cancela ao fechar por overlay/ESC/Cancelar — não no Action de confirmar.
        if (!v) onCancel();
      }}
    >
      <AlertDialogContent className="z-[90] rounded-xl border-border bg-surface-card shadow-lg">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-base font-bold uppercase tracking-wide text-text">
            {title}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-[15px] leading-snug text-text-muted">
            {message}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2">
          <AlertDialogCancel
            onClick={onCancel}
            className="min-h-btn rounded-xl border-2 border-brand-navy bg-surface-card text-brand-navy"
          >
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            className="min-h-btn rounded-xl bg-brand-navy text-primary-foreground hover:bg-brand-navy-deep"
            onClick={(e) => {
              e.preventDefault();
              onConfirm();
            }}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </RadixAlertDialog>
  );
}
