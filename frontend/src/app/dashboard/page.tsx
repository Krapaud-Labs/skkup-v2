import type { Metadata } from "next";
import { ViewerDashboard } from "@/components/dashboard/ViewerDashboard";

export const metadata: Metadata = {
  title: "Tableau de bord | Skkup",
  description: "Retrouve ton solde de points et ta progression Skkup.",
  robots: { index: false, follow: false },
};

export default function DashboardPage() {
  return <ViewerDashboard />;
}
