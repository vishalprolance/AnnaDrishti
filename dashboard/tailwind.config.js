/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#10b981', // green for agriculture
        secondary: '#3b82f6', // blue for tech
      },
    },
  },
  plugins: [],
}
