// const path = require("path");
import * as path from "path";

const symlinks = ["postcss.config.js", ".eslintrc.json"];

export class LinterHooks {
  constructor(jsRelPath, isNextJS) {
    this.jsRelPath = jsRelPath;
    this.isNextJS = isNextJS;
  }

  relpath = (f) => {
    return path.relative(path.join(process.cwd(), this.jsRelPath), f);
  };

  abspath = (f) => {
    return path.join(process.cwd(), this.jsRelPath, f);
  };

  prettier = (filenames) => {
    return `prettier --write ${filenames
      .map(this.relpath)
      .filter((f) => symlinks.indexOf(f) === -1)
      .join(" ")}`;
  };

  eslint = (filenames) => {
    if (this.isNextJS) {
      return `next lint --fix --file ${filenames.join(" --file ")}`;
    } else {
      return `eslint -c ${this.abspath(
        ".eslintrc.json",
      )} --fix ${filenames.join(" ")}`;
    }
  };
}
