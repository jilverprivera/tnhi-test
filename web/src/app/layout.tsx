import type { Metadata, Viewport } from "next";
import { Manrope, Outfit } from "next/font/google";

import { ServiceWorkerProvider } from "@/shared/ui/organisms/ServiceWorkerProvider";
import { ThemeProvider } from "@/shared/ui/organisms/ThemeProvider";
import { Toaster } from "@/shared/ui/primitives/sonner";
import { TooltipProvider } from "@/shared/ui/primitives/tooltip";

import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], display: "swap", variable: "--font-manrope" });
const outfit = Outfit({ subsets: ["latin"], display: "swap", variable: "--font-outfit" });

export const metadata: Metadata = {
  title: { default: "Docket · Radicación TAC", template: "%s · Docket" },
  description: "Radicación asistida de correspondencia para Terminales Andinas de Carga.",
  applicationName: "Docket",
  appleWebApp: { capable: true, title: "Docket", statusBarStyle: "default" },
  icons: { icon: "/icons/icon-192.png", apple: "/icons/apple-touch-icon.png" },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fff9f3" },
    { media: "(prefers-color-scheme: dark)", color: "#0e0c09" },
  ],
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-CO" className={`${manrope.variable} ${outfit.variable}`} suppressHydrationWarning>
      <body>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2">
          Saltar al contenido
        </a>
        <ServiceWorkerProvider>
          <ThemeProvider>
            <TooltipProvider>{children}</TooltipProvider>
            <Toaster richColors position="top-center" />
          </ThemeProvider>
        </ServiceWorkerProvider>
      </body>
    </html>
  );
}
