import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        agent: {
          pm: { DEFAULT: '#8B5CF6', light: '#EDE9FE' },
          dev: { DEFAULT: '#3B82F6', light: '#DBEAFE' },
          qa: { DEFAULT: '#10B981', light: '#D1FAE5' },
          architect: { DEFAULT: '#F59E0B', light: '#FEF3C7' },
          designer: { DEFAULT: '#EC4899', light: '#FCE7F3' },
          devops: { DEFAULT: '#6366F1', light: '#E0E7FF' },
        },
        status: {
          backlog: '#9CA3AF',
          'in-progress': '#3B82F6',
          'in-review': '#F59E0B',
          done: '#10B981',
          failed: '#EF4444',
          blocked: '#6B7280',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config;
