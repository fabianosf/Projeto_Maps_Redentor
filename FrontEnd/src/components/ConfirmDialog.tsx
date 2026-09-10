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
      <AlertDialogContent className="z-[90] border-border bg-card shadow-lg">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-base font-bold uppercase tracking-wide text-foreground">
            {title}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-[15px] leading-snug text-muted-foreground">
            {message}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2 sm:gap-2">
          <AlertDialogCancel
            onClick={onCancel}
            className="min-h-touch"
          >
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            className="min-h-touch"
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
