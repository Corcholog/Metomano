/** @type {import('tailwindcss').Config} */
module.exports = {
  plugins: {
    content: [
      './pages/**/*.{js,ts,jsx,tsx}',
      './components/**/*.{js,ts,jsx,tsx}',
    ],
    tailwindcss: {},
    autoprefixer: {},
  },
}
