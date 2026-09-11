/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './dashboard/templates/**/*.html',
    './dashboard/**/*.py',
    './dashboard_interna/templates/**/*.html'
  ],
  theme: {
    extend: {
      colors: {
        'usm-blue': '#004B87',
        'usm-dark': '#00335c',
        'diftel-yellow': '#FFB81C',
        'diftel-cyan': '#00B5E2',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: [
      {
        diftel: {
          "primary": "#004B87",
          "secondary": "#00B5E2",
          "accent": "#FFB81C",
          "neutral": "#00335c",
          "base-100": "#f8fafc",
          "info": "#00B5E2",
          "success": "#36D399",
          "warning": "#FFB81C",
          "error": "#F87272",
        },
      },
      "light",
      "dark",
    ],
  },
}
