"use client";
import { useState } from "react";
import { clsx } from "clsx";
import { Play, Loader2, Code2, FileText, Sparkles } from "lucide-react";

export type CodeType = "openscad" | "build123d";
export type Mode = "describe" | "paste";
export type PromptPayload = {
  mode: Mode;
  prompt: string;
  code: string;
  codeType: CodeType;
  dims: { x?: number; y?: number; z?: number };
};

export interface PromptBoxProps {
  onSubmit: (payload: PromptPayload) => void;
  running: boolean;
}

const SAMPLE_BUILD123D = `# Electronic enclosure base (50x40x20mm) with cutout and mounting holes
from build123d import *

with BuildPart() as bp:
    with BuildSketch() as sk:
        Rectangle(50, 40)
        fillet(sk.vertices(), radius=3)
    extrude(amount=20)
    # Hollow the inside, leaving 2mm walls and floor
    offset(amount=-2, mode=Mode.SUBTRACT)
    # Top cutout for cable pass-through
    with Locations((0, 0, 20)):
        with BuildSketch() as cut:
            Rectangle(20, 6)
        extrude(amount=-5, mode=Mode.SUBTRACT)
    # M3 mounting holes
    for x in (-20, 20):
        for y in (-14, 14):
            with Locations((x, y, 0)):
                Hole(radius=1.6, depth=20)

part = bp.part
`;

const SAMPLE_OPENSCAD = `// L-shaped mounting bracket, 40x30x20mm, two M3 screw holes
$fn = 48;

module m3_hole(h = 20) {
    cylinder(h = h, r = 1.6, center = true);
}

module bracket() {
    difference() {
        union() {
            translate([0, 0, 0])
                cube([40, 30, 4], center = false);
            translate([0, 0, 4])
                cube([4, 30, 16], center = false);
        }
        translate([12, 15, 0]) m3_hole(h = 8);
        translate([28, 15, 0]) m3_hole(h = 8);
        translate([12, 15, 3.2]) cylinder(h = 1, r = 3.0, center = true);
        translate([28, 15, 3.2]) cylinder(h = 1, r = 3.0, center = true);
    }
}

bracket();
`;

export default function PromptBox({ onSubmit, running }: PromptBoxProps) {
  const [mode, setMode] = useState<Mode>("describe");
  const [prompt, setPrompt] = useState(
    "An L-shaped mounting bracket, 40x30x20mm, with two M3 screw holes on the long arm."
  );
  const [code, setCode] = useState("");
  const [codeType, setCodeType] = useState<CodeType>("build123d");
  const [dx, setDx] = useState("");
  const [dy, setDy] = useState("");
  const [dz, setDz] = useState("");

  const canSubmit = mode === "describe" ? prompt.trim().length > 0 : code.trim().length > 0;

  function loadSample(type: "build123d" | "openscad") {
    setMode("paste");
    if (type === "build123d") {
      setCode(SAMPLE_BUILD123D);
      setCodeType("build123d");
      setDx("50");
      setDy("40");
      setDz("20");
    } else {
      setCode(SAMPLE_OPENSCAD);
      setCodeType("openscad");
      setDx("40");
      setDy("30");
      setDz("20");
    }
  }

  function submit() {
    if (!canSubmit || running) return;
    const dims = {
      x: dx ? Number(dx) : undefined,
      y: dy ? Number(dy) : undefined,
      z: dz ? Number(dz) : undefined,
    };
    onSubmit({ mode, prompt, code, codeType, dims });
  }

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="inline-flex rounded-lg bg-overlay/60 p-0.5">
          {(["describe", "paste"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={clsx(
                "flex items-center gap-1.5 rounded-[0.375rem] px-2.5 py-1 text-xs transition-[color,background-color] duration-150",
                mode === m ? "bg-accent/15 text-accent" : "text-mid hover:text-hi"
              )}
            >
              {m === "describe" ? <FileText className="h-3 w-3" /> : <Code2 className="h-3 w-3" />}
              {m === "describe" ? "Describe" : "Paste code"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-2xs text-mid">
          <span className="text-lo">Presets:</span>
          <button
            type="button"
            onClick={() => loadSample("build123d")}
            className="rounded border border-hi bg-overlay/40 px-2 py-0.5 hover:text-hi transition-colors"
          >
            Enclosure (build123d)
          </button>
          <button
            type="button"
            onClick={() => loadSample("openscad")}
            className="rounded border border-hi bg-overlay/40 px-2 py-0.5 hover:text-hi transition-colors"
          >
            Bracket (OpenSCAD)
          </button>
        </div>
      </div>

      {mode === "describe" ? (
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe a mechanical bracket or enclosure…"
          aria-label="Part description"
          className="min-h-[88px] flex-1 resize-none rounded-lg bg-overlay/40 border border-hi px-3 py-2 text-sm text-hi placeholder:text-lo focus:outline-none focus:border-accent/40"
        />
      ) : (
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste build123d or OpenSCAD code…"
          aria-label="CAD source code"
          spellCheck={false}
          className="min-h-[88px] flex-1 resize-none rounded-lg bg-overlay/40 border border-hi px-3 py-2 font-mono text-2xs text-hi placeholder:text-lo focus:outline-none focus:border-accent/40"
        />
      )}

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={codeType}
          aria-label="CAD code type"
          onChange={(e) => setCodeType(e.target.value as CodeType)}
          className="rounded-lg bg-overlay/40 border border-hi px-2 py-1.5 text-xs text-hi focus:outline-none focus:border-accent/40"
        >
          <option value="build123d">build123d</option>
          <option value="openscad">OpenSCAD</option>
        </select>
        <div className="flex items-center gap-1.5 text-2xs text-mid">
          <span className="text-lo">dims mm</span>
          {(["x", "y", "z"] as const).map((k) => (
            <input
              key={k}
              type="number"
              placeholder={k}
              value={k === "x" ? dx : k === "y" ? dy : dz}
              onChange={(e) => {
                const s = e.target.value;
                if (k === "x") setDx(s);
                else if (k === "y") setDy(s);
                else setDz(s);
              }}
              aria-label={`Target ${k} dimension in millimetres`}
              className="w-12 rounded-md bg-overlay/40 border border-hi px-1.5 py-1 text-xs tabular text-hi placeholder:text-lo focus:outline-none focus:border-accent/40"
            />
          ))}
        </div>
      </div>

      <button
        onClick={submit}
        disabled={!canSubmit || running}
        className={clsx(
          "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          canSubmit && !running
            ? "bg-accent/15 text-accent hover:bg-accent/25 border border-accent/30"
            : "bg-overlay/40 text-lo border border-hi cursor-not-allowed"
        )}
      >
        {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
        {running ? "Running…" : mode === "describe" ? "Generate" : "Validate"}
      </button>
    </div>
  );
}
