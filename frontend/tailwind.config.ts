import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';

export default {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        background: '#0b1220',
        foreground: '#f8fafc',
        card: '#111827',
        'card-foreground': '#f8fafc',
        primary: '#2563eb',
        secondary: '#7c3aed',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
        border: 'rgba(255, 255, 255, 0.1)',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(255,255,255,0.06), 0 24px 80px rgba(37,99,235,0.24)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [tailwindcssAnimate],
} satisfies Config;
