import type { Metadata } from "next";
import { AuthExperience } from "@/components/auth/AuthExperience";

export const metadata: Metadata = {
  title: "Connexion | Skkup",
  description:
    "Connecte-toi pour retrouver tes points, ta série de visites et tes cartes à gratter.",
  alternates: { canonical: "/connexion" },
  robots: { index: false, follow: false },
};

export default function ConnexionPage() {
  return <AuthExperience mode="connexion" />;
}
