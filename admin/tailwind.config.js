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
        admin: {
          50: "#f6f6f9",
          100: "#ececf1",
          200: "#d5d5e0",
          300: "#b1b1c6",
          400: "#8686a7",
          500: "#65658b",
          600: "#505072",
          700: "#41415d",
          800: "#38384d",
          900: "#1f1f2e",
          950: "#13131d",
        },
      },
    },
  },
  plugins: [],
}
