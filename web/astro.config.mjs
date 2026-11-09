import { defineConfig } from 'astro/config';
import tailwind from '@tailwindcss/vite';

export default defineConfig({
  output: 'static',
  outDir: './built',
  build: { inlineStylesheets: 'never' },
  vite: { plugins: [tailwind()], build: { assetsInlineLimit: 0 } },
});
