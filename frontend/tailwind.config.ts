import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas:  "#090c11",
        surface: "#0f1319",
        raised:  "#151b23",
        overlay: "#1c242f",
        border:  "rgba(255,255,255,0.07)",
        accent:  "#56b4e9",
        "accent-dim": "#2d7dab",
        hi:    "#e5e7eb",
        mid:   "#8b95a6",
        lo:    "#505968",
        pass:  "#4ade80",
        fail:  "#f87171",
        warn:  "#facc15",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-mono)", "ui-monospace", "Menlo"],
      },
      borderRadius: {
        "2.5xl": "1.125rem",
      },
      fontSize: {
        "2xs": ["0.65rem", "0.9rem"],
      },
      fontVariantNumeric: ["tabular-nums"],
    },
  },
  plugins: [],
};

export default config;
