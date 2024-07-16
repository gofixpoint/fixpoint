import { LinterHooks } from "./linterhooks.mjs";

const linterhooks = new LinterHooks("js/__shared__", false);

export default {
  "*.{mjs,js,jsx,ts,tsx}": [linterhooks.eslint, linterhooks.prettier],
  "*.{json,md}": linterhooks.prettier,
};
