/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0A192F',
          800: '#112240',
          700: '#233554',
        },
        accent: {
          neon: '#64FFDA',
          blue: '#448AFF',
          purple: '#B388FF',
          pink: '#FF80AB',
          yellow: '#FFD740',
          red: '#FF5252',
          green: '#69F0AE'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
