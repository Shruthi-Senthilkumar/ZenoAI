"use client";

interface StateBlockProps {
  variant?: "empty" | "error" | "not-connected";
  tag?: string;
  message: string;
  ctaLabel?: string;
  onCta?: () => void;
}

export function StateBlock({
  variant = "empty",
  tag,
  message,
  ctaLabel,
  onCta,
}: StateBlockProps) {
  const className =
    variant === "error"
      ? "state-block error"
      : variant === "not-connected"
      ? "state-block not-connected"
      : "state-block";

  return (
    <div className={className}>
      {tag && <span className="state-tag">{tag}</span>}
      <p>{message}</p>
      {ctaLabel && onCta && (
        <button className="state-cta" onClick={onCta}>
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
