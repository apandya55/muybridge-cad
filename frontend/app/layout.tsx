import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Muybridge CAD | Part verification",
  description:
    "Build or inspect a mechanical part, then check its geometry from several views.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-canvas">{children}</body>
    </html>
  );
}
