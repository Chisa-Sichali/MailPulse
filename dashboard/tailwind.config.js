/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ["Urbanist", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.65rem", { lineHeight: "0.875rem" }],
        "xs": ["0.8rem", { lineHeight: "1.125rem" }],
        "sm": ["0.925rem", { lineHeight: "1.375rem" }],
        "base": ["1rem", { lineHeight: "1.5rem" }],
      },
      colors: {
        surface: {
          DEFAULT: "var(--surface)",
          muted: "var(--surface-muted)",
          border: "var(--surface-border)",
        },
        ink: {
          DEFAULT: "var(--ink)",
          muted: "var(--ink-muted)",
          faint: "var(--ink-faint)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
          hover: "var(--accent-hover)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          hover: "var(--sidebar-hover)",
          border: "var(--sidebar-border)",
        },
      },
    },
  },
  plugins: [],
};

