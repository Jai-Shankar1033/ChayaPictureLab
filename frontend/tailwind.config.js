import animate from 'tailwindcss-animate'
/** @type {import('tailwindcss').Config} */
export default { darkMode: ['class'], content: ['./index.html', './src/**/*.{ts,tsx}'], theme: { extend: { colors: { background: '#080b14', foreground: '#f4f7fb', card: '#101521', primary: '#54e3e6', muted: '#8e9aaa', border: '#ffffff16' } } }, plugins: [animate] }
