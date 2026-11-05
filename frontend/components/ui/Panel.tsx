"use client";
import { clsx } from "clsx";

export default function Panel({
  title,
  children,
  className,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={clsx(
        "relative flex flex-col rounded-2.5xl bg-surface/80 border border-hi backdrop-blur-sm overflow-hidden",
        className,
      )}
    >
      {title && (
        <div className="flex items-center justify-between px-4 pt-3 pb-2">
          <h2 className="font-mono text-xs text-mid">
            {title}
          </h2>
        </div>
      )}
      <div className="flex-1 min-h-0 p-4 pt-0">{children}</div>
    </section>
  );
}
