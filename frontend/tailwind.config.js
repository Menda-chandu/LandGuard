/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f4f9',
          100: '#d9e2ec',
          500: '#1b365d', // Govt Navy
          600: '#102a43',
          700: '#0b1b2b',
          accent: '#008080', // Teal accent
          alert: '#d9381e',
          warning: '#e67e22',
          success: '#27ae60'
        }
      }
    },
  },
  plugins: [],
}
