/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        void: '#0A0A0A',
        surface: '#141414',
        ink: {
          DEFAULT: '#EDEDED',
          muted: '#888888',
        },
        clarity: '#2563EB',
        truth: {
          green: '#16A34A',
          amber: '#D97706',
          red: '#DC2626',
        }
      },
      fontFamily: {
        narrative: ['Inter', 'sans-serif'],
        data: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
