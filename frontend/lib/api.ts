/**
 * API helpers and the event stream reader used by the studio.
 */

export type SSEEventType =
  | "start" | "compiling" | "assertions" | "plate"
  | "critique" | "fix" | "success" | "failed" | "error";

export interface Assertion {
  name: string;
  passed: boolean;
  value?: string | number | null;
  threshold?: string | number | null;
  message: string;
}

export interface CritiqueResult {
  approved: boolean;
  errors: string[];
  critique: string;
  suggested_code: string;
}

export interface SSEEvent {
  type: SSEEventType;
  iteration: number;
  message?: string;
  code?: string;
  code_type?: string;
  assertions?: Assertion[];
  plate_url?: string;
  stl_url?: string;
  critique?: CritiqueResult;
  job_id?: string;
}

export interface GeneratePayload {
  prompt: string;
  code_type: "openscad" | "build123d";
  requested_dims?: { x?: number; y?: number; z?: number };
}

export interface ValidatePayload {
  code: string;
  code_type: "openscad" | "build123d";
  requested_dims?: { x?: number; y?: number; z?: number };
}

/**
 * Read the event stream and forward each parsed event to the caller.
 */
export function consumeSSE(
  url: string,
  body: object,
  onEvent: (e: SSEEvent) => void,
  onDone: () => void,
  onError: (msg: string) => void,
): AbortController {
  const ctrl = new AbortController();
  (async () => {
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      if (!resp.ok) {
        onError(`HTTP ${resp.status}: ${await resp.text()}`);
        return;
      }
      if (!resp.body) {
        onError("The server returned an empty event stream.");
        return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const chunks = buf.split("\n\n");
        buf = chunks.pop() ?? "";
        for (const chunk of chunks) {
          const dataLine = chunk.split("\n").find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          try {
            const event = JSON.parse(dataLine.slice(5).trim()) as SSEEvent;
            onEvent(event);
          } catch {
            // A partial event will be retried when more data arrives.
          }
        }
      }
      if (buf.trim()) {
        const dataLine = buf.split("\n").find((l) => l.startsWith("data:"));
        if (dataLine) {
          try {
            onEvent(JSON.parse(dataLine.slice(5).trim()) as SSEEvent);
          } catch {
            // Leave incomplete trailing data alone.
          }
        }
      }
      onDone();
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") {
        onError(String(err));
      }
    }
  })();
  return ctrl;
}
