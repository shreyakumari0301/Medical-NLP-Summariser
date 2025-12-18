import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Physician Notetaker",
  description: "Medical transcription, summarization, sentiment & SOAP generation"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div className="main-container py-10">{children}</div>
      </body>
    </html>
  );
}

