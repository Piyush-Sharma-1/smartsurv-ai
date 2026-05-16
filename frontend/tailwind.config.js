/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0fdf4",
          500: "#22c55e",
          600: "#16a34a",
          900: "#14532d",
        },
        dark: {
          900: "#0a0f14",
          800: "#111827",
          700: "#1f2937",
          600: "#374151",
        }
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
        sans: ["'DM Sans'", "sans-serif"],
      }
    },
  },
  plugins: [],
}