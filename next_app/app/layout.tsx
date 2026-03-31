import type { Metadata } from "next";
import { DM_Serif_Display, Inter } from "next/font/google";
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
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${dmSerif.variable} ${inter.variable}`} suppressHydrationWarning>
        <AuthProvider>
          <DashboardLayoutClient>
            {children}
          </DashboardLayoutClient>
        </AuthProvider>
      </body>
    </html>
  );
}
