"use client";
import { CircleCheck, CircleX } from "lucide-react";
import type { Assertion } from "@/lib/api";

export default function AssertionPanel({
  assertions,
}: {
  assertions: Assertion[];
}) {
  if (assertions.length === 0) {
    return (
      <div className="flex h-full min-h-[100px] items-center justify-center text-2xs text-lo">
        Run a part to see the checks.
      </div>
    );
  }

  const allPass = assertions.every((a) => a.passed);
  const allFail = assertions.every((a) => !a.passed);

  return (
    <div className="flex flex-col gap-2">
      <div
        className={`mb-1 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium ${
          allPass
            ? "bg-pass/10 text-pass"
            : allFail
              ? "bg-fail/10 text-fail"
              : "bg-warn/10 text-warn"
        }`}
      >
        {allPass ? "All checks pass" : allFail ? "All checks failed" : "Some checks need work"}
      </div>

      {assertions.map((a) => (
          <div
            key={a.name}
            className="flex items-start gap-2.5 rounded-lg bg-overlay/40 px-3 py-2.5"
          >
            <span className="mt-0.5 shrink-0">
              {a.passed ? (
                <CircleCheck className="h-3.5 w-3.5 text-pass" />
              ) : (
                <CircleX className="h-3.5 w-3.5 text-fail" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-mid">
                  {a.name}
                </span>
                {a.value != null && (
                  <span className="tabular shrink-0 font-mono text-2xs text-hi">
                    {String(a.value)}
                  </span>
                )}
              </div>
              {a.message && (
                <div className="mt-0.5 text-2xs text-lo leading-tight">{a.message}</div>
              )}
              {a.threshold != null && (
                <div className="mt-0.5 tabular text-2xs text-lo">
                  threshold: {String(a.threshold)}
                </div>
              )}
            </div>
          </div>
        ))}
    </div>
  );
}
