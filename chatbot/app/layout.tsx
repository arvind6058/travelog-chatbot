import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TravelLogix - Travel & Logistics in One Chat",
  description: "AI-powered Travel and Logistics platform for modern logistics tracking and unified travel management.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
