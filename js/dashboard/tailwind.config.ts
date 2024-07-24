import deepmerge from "deepmerge";

import {
  shadcnTheme,
  tremorTheme,
  tremorSafelist,
} from "../__shared__/tailwind-config-helpers";

/** @type {import('tailwindcss').Config} */
const shadcnConfig = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: shadcnTheme,
  plugins: [require("tailwindcss-animate")],
};

/** @type {import('tailwindcss').Config} */
const tremorConfig = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  theme: tremorTheme,
  safelist: tremorSafelist,
  plugins: [require("@headlessui/tailwindcss")],
};

/** @type {import('tailwindcss').Config} */
const config = deepmerge.all([tremorConfig, shadcnConfig]);
export default config;
