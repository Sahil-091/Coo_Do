"use client";

import { X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/cn";
import { Button } from "./Button";

export interface AdaptivePanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Renders as a bottom sheet on mobile and a right-side panel on desktop
 * — purely via CSS breakpoints (`md:`), not two components or a JS
 * viewport check. Real dialog semantics: focus moves in on open, Tab is
 * trapped inside, Escape closes, focus returns to whatever triggered it,
 * background scroll is locked while open.
 */
export function AdaptivePanel({ open, onClose, title, children, className }: AdaptivePanelProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const [animateIn, setAnimateIn] = useState(false);

  // Remember what had focus before opening, restore it on close.
  useEffect(() => {
    if (open) {
      triggerRef.current = document.activeElement as HTMLElement | null;
    } else {
      triggerRef.current?.focus();
    }
  }, [open]);

  // Move focus in, lock background scroll, and kick off the entrance
  // transition on the next frame (so it actually transitions rather
  // than snapping in at its final position).
  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    panelRef.current?.focus();
    const raf = requestAnimationFrame(() => setAnimateIn(true));
    return () => {
      document.body.style.overflow = previousOverflow;
      cancelAnimationFrame(raf);
      setAnimateIn(false);
    };
  }, [open]);

  // Escape closes; Tab is trapped within the panel while open.
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;
      const focusable = panelRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (typeof document === "undefined" || !open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50">
      <div
        className={cn(
          "absolute inset-0 bg-ink/30 transition-opacity duration-200",
          animateIn ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={cn(
          "absolute max-h-[85vh] overflow-y-auto rounded-t-xl bg-paper-raised shadow-xl outline-none transition-transform duration-200 ease-out",
          "inset-x-0 bottom-0",
          "md:inset-x-auto md:inset-y-0 md:right-0 md:bottom-auto md:h-full md:w-96 md:max-h-none md:rounded-t-none md:rounded-l-xl",
          animateIn ? "translate-y-0 md:translate-x-0" : "translate-y-full md:translate-x-full md:translate-y-0",
          className
        )}
      >
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-4">
          <h2 id={titleId} className="font-display text-lg text-ink">
            {title}
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" aria-hidden="true" />
          </Button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>,
    document.body
  );
}
