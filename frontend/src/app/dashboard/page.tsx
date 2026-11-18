import type { Metadata } from "next";
import { DashboardEntry } from "@/components/dashboard/DashboardEntry";

export const metadata: Metadata = {
  title: "Tableau de bord | Skkup",
  description: "Retrouve ton espace personnel ou d’administration Skkup.",
  robots: { index: false, follow: false },
};

export default function DashboardPage() {
  return <DashboardEntry />;
}
