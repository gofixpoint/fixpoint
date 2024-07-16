import React from "react";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { RootProvider } from "@/provider";
import { loadEnv } from "@/env";
import Navbar from "@/components/navigation/navbar";
import { Toaster } from "@/components/ui/toaster";

// Force dynamic rendering on all routes using this layout.
// This makes sure that we use the environment variable values from runtime
// instead of buildtime.
export const dynamic = "force-dynamic";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fixpoint",
  description: "Open source infra for reliable multi-step AI workflows",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const env = loadEnv();

  return (
    <html lang="en">
      <body
        className={cn(
          inter.className,
          "min-h-screen max-h-screen bg-background font-sans antialiased",
          "overflow-y-clip",
          "bg-background",
          "dark",
        )}
      >
        <RootProvider env={env}>
          <div className="flex flex-row h-screen max-h-screen">
            <Navbar />
            <div className="w-full h-screen max-h-screen overflow-y-auto">
              {children}
            </div>
          </div>
        </RootProvider>
        <Toaster />
      </body>
    </html>
  );
}
