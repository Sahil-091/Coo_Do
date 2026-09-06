import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef } from "react";
import { cn } from "@/lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-lamp text-white hover:bg-lamp/90 active:bg-lamp/80",
        secondary:
          "bg-paper-raised text-ink border border-border hover:bg-paper active:bg-paper",
        ghost: "bg-transparent text-ink-muted hover:bg-lamp-tint hover:text-ink",
        "quiet-destructive": "bg-transparent text-clay hover:bg-clay-tint",
      },
      size: {
        default: "h-11 px-5",
        sm: "h-9 px-3.5",
        /** Icon-only — caller MUST supply an aria-label, this size never renders visible text. */
        icon: "h-11 w-11 shrink-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...props }, ref) => {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
