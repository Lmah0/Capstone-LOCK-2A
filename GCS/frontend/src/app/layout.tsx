import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LOCK-2A GCS",
  description: "Ground Control Station for LOCK-2A",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode; }>) 
{
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
