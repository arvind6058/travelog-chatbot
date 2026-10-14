/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8ff",
          100: "#d8eeff",
          200: "#b9e2ff",
          300: "#89d0ff",
          400: "#52b3ff",
          500: "#2a92ff",
          600: "#1372f6",
          700: "#0d5bdf",
          800: "#114ab4",
          900: "#14408d",
          950: "#112956",
        },
      },
    },
  },
  plugins: [],
}
