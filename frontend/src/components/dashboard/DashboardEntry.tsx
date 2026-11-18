"use client";

import { useEffect, useState } from "react";
import { AdminDashboard } from "@/components/dashboard/AdminDashboard";
import { ViewerDashboard } from "@/components/dashboard/ViewerDashboard";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Profile = Readonly<{ id: string; pseudo: string; email: string; role: string }>;
type Session = Readonly<{ authentifie?: boolean; profil?: Profile | null }>;

export function DashboardEntry() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    fetch(`${apiBase}/auth/session`, { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Session unavailable");
        return response.json() as Promise<Session>;
      })
      .then((session) => {
        if (!active) return;
        if (session.authentifie !== true || !session.profil) {
          window.location.replace("/connexion");
          return;
        }
        if (session.profil.role !== "VIEWER" && session.profil.role !== "ADMIN") {
          setFailed(true);
          return;
        }
        setProfile(session.profil);
      })
      .catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, []);

  if (profile?.role === "ADMIN") return <AdminDashboard profile={profile} />;
  if (profile?.role === "VIEWER") return <ViewerDashboard />;

  return (
    <main className="viewer-dashboard dashboard-entry-state">
      <section className="vd-panel" role={failed ? "alert" : "status"}>
        {failed ? "Impossible de vérifier ta session. Réessaie dans quelques instants." : "Ouverture de ton espace Skkup…"}
      </section>
    </main>
  );
}
