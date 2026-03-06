/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0d1117',
        surface: '#161b22',
        border: '#30363d',
        accent: '#58a6ff',
        success: '#3fb950',
        error: '#f85149',
        'text-primary': '#e6edf3',
        muted: '#8b949e',
      },
    },
  },
  plugins: [],
}

