import type { Metadata } from "next";
import { DM_Serif_Display, Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import DashboardLayoutClient from "@/components/DashboardLayoutClient";
import { AuthProvider } from "@/lib/auth-context";

const dmSerif = DM_Serif_Display({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-serif",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "AI Oracle",
  description: "Astrological Intelligence Engine",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Abu Oracle",
  },
  formatDetection: { telephone: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const paddleToken = process.env.NEXT_PUBLIC_PADDLE_TOKEN ?? "";

  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Abu Oracle" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        <meta name="theme-color" content="#f59e0b" />
      </head>
      <body className={`${dmSerif.variable} ${inter.variable}`} suppressHydrationWarning>
        <AuthProvider>
          <DashboardLayoutClient>
            {children}
          </DashboardLayoutClient>
        </AuthProvider>

        {/* Paddle.js - only loads in browser */}
        <Script src="https://cdn.paddle.com/paddle/v2/paddle.js" strategy="afterInteractive" />
        {paddleToken && (
          <Script
            id="paddle-init"
            strategy="afterInteractive"
            dangerouslySetInnerHTML={{
              __html: `
                (function initPaddle() {
                  if (window.Paddle) {
                    window.Paddle.Initialize({ token: ${JSON.stringify(paddleToken)} });
                    return;
                  }
                  window.setTimeout(initPaddle, 100);
                })();
              `,
            }}
          />
        )}
      </body>
    </html>
  );
}
