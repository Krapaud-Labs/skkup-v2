import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./auth.css";

export const metadata: Metadata = {
  title: "Skkup",
  description: "Ton espace Skkup.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
