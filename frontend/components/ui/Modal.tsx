"use client";

import { useEffect, useRef } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="backdrop:bg-black/40 bg-canvas border border-border-warm rounded-[10px] p-6 max-w-md w-full shadow-none"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-text-primary">{title}</h2>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text-primary transition-colors text-xl leading-none cursor-pointer"
          aria-label="Close"
        >
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}
