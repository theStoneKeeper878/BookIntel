import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "BookIntel — Document Intelligence Platform",
  description:
    "AI-powered book intelligence platform with RAG-based question answering, automated scraping, and smart insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ position: 'relative', zIndex: 1 }}>
        <Navbar />
        <main
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '24px',
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
