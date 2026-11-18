import type { Metadata } from "next";
import { AuthExperience } from "@/components/auth/AuthExperience";

export const metadata: Metadata = {
  title: "Inscription | Skkup",
  description:
    "Crée ton compte Skkup et gagne des points en regardant tes streams préférés.",
  alternates: { canonical: "/inscription" },
  robots: { index: false, follow: false },
};

export default function InscriptionPage() {
  return <AuthExperience mode="inscription" />;
}
