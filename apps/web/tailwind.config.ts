import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        app: "var(--color-bg-app)",
        panel: "var(--color-bg-panel)",
        surface: "var(--color-bg-surface)",
        border: "var(--color-border)",
        ink: {
          DEFAULT: "var(--color-text-primary)",
          muted: "var(--color-text-secondary)",
          subtle: "var(--color-text-tertiary)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          strong: "var(--color-accent-strong)",
        },
        socrates: "var(--color-socrates)",
        evidence: "var(--color-evidence)",
        success: "var(--color-success)",
        warning: "var(--color-warning)",
        danger: "var(--color-danger)",
      },
      boxShadow: {
        panel: "0 1px 2px rgba(16, 24, 40, 0.06), 0 12px 28px rgba(35, 48, 72, 0.07)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
