"use client";
import { useReducer, useRef, useState } from "react";
import Panel from "@/components/ui/Panel";
import PromptBox, { type PromptPayload } from "@/components/PromptBox";
import MuybridgePlate from "@/components/MuybridgePlate";
import AssertionPanel from "@/components/AssertionPanel";
import ThreeViewport from "@/components/ThreeViewport";
import CriticLog, { type CriticEntry } from "@/components/CriticLog";
import { consumeSSE, type Assertion, type SSEEvent } from "@/lib/api";

interface State {
  status: "idle" | "running" | "success" | "failed" | "error";
  iteration: number;
  stlUrl: string | null;
  plateUrl: string | null;
  assertions: Assertion[];
  critiques: CriticEntry[];
  message: string;
  error: string | null;
}

const initial: State = {
  status: "idle", iteration: 0,
  stlUrl: null, plateUrl: null, assertions: [], critiques: [],
  message: "", error: null,
};

type Action =
  | { type: "reset" }
  | { type: "event"; e: SSEEvent }
  | { type: "error"; msg: string }
  | { type: "done" };

function reducer(state: State, action: Action): State {
  if (action.type === "reset") return { ...initial };
  if (action.type === "error") return { ...state, status: "error", error: action.msg };
  if (action.type === "done") {
    if (state.status === "running") return { ...state, status: "idle" };
    return state;
  }
  const e = action.e;
  let s: State = { ...state, message: e.message ?? state.message };
  switch (e.type) {
    case "start":
      return { ...s, status: "running" };
    case "compiling":
      return { ...s, status: "running", iteration: e.iteration || s.iteration, message: e.message ?? s.message };
    case "assertions":
      return { ...s, assertions: e.assertions ?? s.assertions };
    case "plate":
      return {
        ...s,
        plateUrl: e.plate_url ? e.plate_url : s.plateUrl,
        stlUrl: e.stl_url ? e.stl_url : s.stlUrl,
      };
    case "critique":
      if (e.critique) {
        return {
          ...s,
          critiques: [...s.critiques, { iteration: e.iteration, critique: e.critique }],
        };
      }
      return s;
    case "fix":
      return { ...s, iteration: e.iteration || s.iteration };
    case "success":
      return { ...s, status: "success", message: e.message ?? s.message };
    case "failed":
      return { ...s, status: "failed", message: e.message ?? s.message };
    case "error":
      return { ...s, status: "error", error: e.message ?? "unknown error" };
    default:
      return s;
  }
}

export default function Studio() {
  const [state, dispatch] = useReducer(reducer, initial);
  const ctrlRef = useRef<AbortController | null>(null);
  const [running, setRunning] = useState(false);

  function handleSubmit(payload: PromptPayload) {
    dispatch({ type: "reset" });
    setRunning(true);
    const url = payload.mode === "describe" ? "/api/generate" : "/api/validate";
    const body =
      payload.mode === "describe"
        ? { prompt: payload.prompt, code_type: payload.codeType, requested_dims: payload.dims }
        : { code: payload.code, code_type: payload.codeType, requested_dims: payload.dims };

    ctrlRef.current = consumeSSE(
      url,
      body,
      (e) => dispatch({ type: "event", e }),
      () => { setRunning(false); dispatch({ type: "done" }); },
      (msg) => { setRunning(false); dispatch({ type: "error", msg }); },
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 lg:grid-rows-[auto_1fr] gap-3 lg:gap-4 lg:h-[calc(100vh-7rem)]">
      <Panel title="Describe a part" className="lg:col-span-12">
        <PromptBox onSubmit={handleSubmit} running={running} />
      </Panel>

      <Panel title="Model" className="lg:col-span-7 lg:row-span-2 min-h-[320px] lg:min-h-0">
        <ThreeViewport stlUrl={state.stlUrl} />
      </Panel>

      <Panel title="Inspection plate" className="lg:col-span-5 min-h-[200px]">
          <MuybridgePlate plateUrl={state.plateUrl} running={running} />
      </Panel>

      <Panel title="Checks" className="lg:col-span-3 min-h-[180px]">
        <AssertionPanel assertions={state.assertions} />
      </Panel>
      <Panel title="Review notes" className="lg:col-span-2 min-h-[180px]">
        <CriticLog entries={state.critiques} />
      </Panel>

      <div className="lg:col-span-12 flex items-center justify-between rounded-2.5xl bg-surface/60 border border-hi px-4 py-2.5">
        <span className="text-xs text-mid">
          {state.message || (running ? "Checking the part…" : "Ready")}
        </span>
        <span className="tabular font-mono text-xs text-lo">
          pass {state.iteration} · {state.critiques.length} reviews
          {state.error ? ` · ${state.error}` : ""}
        </span>
      </div>
    </div>
  );
}
