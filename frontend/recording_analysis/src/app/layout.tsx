import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LOCK-2A Tracked Object Analysis System",
  description: "Real-time trajectory visualization and control",
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode;}>) 
{
  return (
    <html lang="en" className="h-full w-full">
      <body className="antialiased h-full w-full">
          <div className="flex flex-col h-full w-full">
            {children}
          </div>
      </body>
    </html>
  );
}
