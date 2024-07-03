import React from "react"
import { DocsThemeConfig } from "nextra-theme-docs"
import { Inter } from "next/font/google"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const title =
  "Fixpoint - Open source infra for reliable multi-step AI workflows"
const description =
  "Build and connect multiple AI agents that know your data and work together to run autonomous or human-in-the-loop workflows, so that the humans can focus on more important work."

// See https://github.com/shuding/nextra/blob/main/docs/theme.config.tsx
// for more examples on theme config.

const config: DocsThemeConfig = {
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

  head: () => {
    return (
      <>
        <meta name="msapplication-TileColor" content="#fff" />
        <meta name="theme-color" content="#fff" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta httpEquiv="Content-Language" content="en" />

        <title>
          Fixpoint - Open source infra for reliable multi-step AI workflows
        </title>
        <meta
          name="description"
          content="Build multi-step AI workflows to automate your busy-work"
        />

        {/* favicon */}
        <link
          rel="apple-touch-icon"
          sizes="180x180"
          href="/apple-touch-icon.png"
        />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link
          rel="icon"
          type="image/png"
          sizes="32x32"
          href="/favicon-32x32.png"
        />
        <link
          rel="icon"
          type="image/png"
          sizes="16x16"
          href="/favicon-16x16.png"
        />
        <link rel="manifest" href="/site.webmanifest" />
        <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#5bbad5" />
        <meta name="msapplication-TileColor" content="#da532c" />
        <meta name="theme-color" content="#ffffff" />
        <link
          rel="icon"
          href="/favicon.svg"
          type="image/svg+xml"
          media="(prefers-color-scheme: dark)"
        />
        <link
          rel="icon"
          href="/favicon-32x32.png"
          type="image/png"
          media="(prefers-color-scheme: dark)"
        />

        {/* Facebook Meta Tags */}
        <meta property="og:url" content="https://fixpoint.co/" />
        <meta property="og:type" content="website" />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />

        {/* Twitter Meta Tags */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta property="twitter:site:domain" content="fixpoint.co" />
        <meta property="twitter:url" content="https://fixpoint.co/" />
        <meta name="twitter:title" content={title} />
        <meta name="twitter:description" content={description} />
      </>
    )
  },

  logo: (
    <span className={`font-bold text-xl ${inter.className}`}>fixpoint</span>
  ),

  useNextSeoProps() {
    return {
      titleTemplate: "%s – Fixpoint docs",
      description: "Build multi-step AI workflows to automate your busy-work",
      openGraph: {
        url: "https://docs.fixpoint.co/",
        type: "website",
        title: title,
        description: description,
      },
      twitter: {
        handle: "gofixpoint",
        site: "https://docs.fixpoint.co/",
      },
    }
  },
}

export default config
