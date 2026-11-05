"use client";
import { useState } from "react";
import { ChevronDown, ScanSearch } from "lucide-react";
import type { CritiqueResult } from "@/lib/api";

export interface CriticEntry {
  iteration: number;
  critique: CritiqueResult;
}

export default function CriticLog({ entries }: { entries: CriticEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className="flex h-full min-h-[100px] items-center justify-center text-2xs text-lo">
        No review yet.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2 overflow-y-auto max-h-full">
        {entries.map((e) => (
          <CriticRow key={e.iteration} entry={e} />
        ))}
    </div>
  );
}

function CriticRow({ entry }: { entry: CriticEntry }) {
  const [open, setOpen] = useState(false);
  const c = entry.critique;
  return (
    <div
      className="rounded-lg bg-overlay/40 px-3 py-2.5"
    >
      <div className="flex items-center gap-2">
        <ScanSearch className={`h-3.5 w-3.5 ${c.approved ? "text-pass" : "text-warn"}`} />
        <span className="font-mono text-xs text-mid">
          pass {entry.iteration}
        </span>
        <span
          className={`ml-auto rounded-full px-1.5 py-0.5 text-2xs ${
            c.approved ? "bg-pass/10 text-pass" : "bg-warn/10 text-warn"
          }`}
        >
          {c.approved ? "accepted" : `${c.errors.length} issues`}
        </span>
      </div>

      {c.errors.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {c.errors.map((err, i) => (
            <span
              key={i}
              className="rounded bg-fail/10 px-1.5 py-0.5 text-2xs text-fail"
            >
              {err}
            </span>
          ))}
        </div>
      )}

      {c.critique && (
        <p className="mt-2 text-2xs leading-snug text-lo">{c.critique}</p>
      )}

      {c.suggested_code && (
        <button
          onClick={() => setOpen((v) => !v)}
          className="mt-2 inline-flex items-center gap-1 text-2xs text-accent-dim hover:text-accent"
        >
          <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
          {open ? "hide fix" : "show fix"}
        </button>
      )}
        {open && c.suggested_code && (
          <pre
            className="mt-2 max-h-40 overflow-auto rounded-md bg-canvas/60 border border-hi p-2 font-mono text-[0.6rem] leading-tight text-mid"
          >
            {c.suggested_code}
          </pre>
        )}
    </div>
  );
}
