import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/components/providers/AuthProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta" });

export const metadata: Metadata = {
  title: "FinWise Teen — Your Money, Your Future",
  description: "AI-powered financial planning for young Indians. Get personalized investment advice across stocks, mutual funds, bonds, gold, and more.",
  keywords: "teenage finance, investment planning India, SIP, mutual funds, financial literacy",
  openGraph: {
    title: "FinWise Teen",
    description: "Start your wealth journey today — built for young India.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jakarta.variable}`}>
      <body className="text-white antialiased">
        <div className="living-bg" aria-hidden="true" />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
