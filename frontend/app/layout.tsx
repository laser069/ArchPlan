import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ArchPlan // Core",
  description: "Architectural Systems Design Environment",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // Added 'selection' styles to ensure even text highlighting is monochrome
      className={`
        ${geistSans.variable} 
        ${geistMono.variable} 
        h-full 
        antialiased 
        selection:bg-white 
        selection:text-black
      `}
    >
      <body className="h-full overflow-hidden bg-background text-foreground">
        {/* The 'overflow-hidden' on body is crucial for "App-style" UIs 
          to prevent the whole page from bouncing on mobile or desktop.
        */}
        {children}
      </body>
    </html>
  );
}