/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "Fira Code", "monospace"],
            },
            colors: {
                "workspace-bg": "#0a0a12",
                "sidebar-bg": "#0f0f1b",
                "panel-bg": "#111120",
                "card-bg": "#16162a",
                "border": "#1e1e3a",
                "border-bright": "#2d2d5a",
                "text-primary": "#e8e8ff",
                "text-secondary": "#7878a8",
                "text-muted": "#3d3d60",
                "accent-purple": "#7c5cbf",
                "accent-cyan": "#00c9a7",
                "accent-pink": "#e040fb",
                "heat-low": "#22c55e",
                "heat-med": "#f59e0b",
                "heat-high": "#ef4444",
            },
        },
    },
    plugins: [],
};
