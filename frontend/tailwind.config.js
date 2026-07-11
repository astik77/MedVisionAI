/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          900: '#060b14',
          800: '#0a1120',
          700: '#0f1929',
          600: '#162235',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          glow: '#22d3ee',
        },
        purple: {
          400: '#c084fc',
          500: '#a855f7',
          glow: '#a855f7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'cyan-glow': '0 0 20px rgba(34, 211, 238, 0.3)',
        'purple-glow': '0 0 20px rgba(168, 85, 247, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
    },
  },
  plugins: [],
}
