import React from "react"
import { DocsThemeConfig } from "nextra-theme-docs"
import { Inter } from "next/font/google"

import { cn } from "./src/lib/utils"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const config: DocsThemeConfig = {
  logo: (
    <span className={cn("font-bold text-xl", inter.className)}>fixpoint</span>
  ),
  project: {
    link: "https://github.com/gofixpoint/fixpoint/",
  },
  chat: {
    link: "https://discord.gg/tdRmQQXAhY",
  },
  docsRepositoryBase: "https://github.com/gofixpoint/fixpoint/tree/main/docs",
  footer: {
    text: "Fixpoint Docs",
  },
}

export default config
