"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DashboardShell } from "@/components/dashboard/DashboardShell";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Profile = { pseudo: string; email: string; role: string };
type Summary = { soldePoints: number; streakActuel: number; streakMax: number; derniereVisiteAt: string | null; prochainPalierStreak: number | null; ticketsDisponibles: Record<string, number> };
type Transaction = { id: string; type: string; montant: number; createdAt: string };

const transactionLabels: Record<string, string> = {
  VISITE_QUOTIDIENNE: "Visite quotidienne",
  WATCH_TIME: "Temps de visionnage",
  CARTE_A_GRATTER: "Carte à gratter",
  AJUSTEMENT_ADMIN: "Ajustement Admin",
  SHOP_PURCHASE: "Achat en boutique",
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { ...init, credentials: "include", headers: { ...(init?.headers ?? {}) } });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export function ViewerDashboard() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [activity, setActivity] = useState<Transaction[]>([]);
  const [fullHistory, setFullHistory] = useState<Transaction[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [modal, setModal] = useState<"account" | "history" | null>(null);
  const [error, setError] = useState("");
  const modalTrigger = useRef<HTMLElement | null>(null);
  const modalClose = useRef<HTMLButtonElement>(null);

  const refresh = useCallback(async () => {
    const [points, history] = await Promise.all([
      api<Summary>("/me/points"),
      api<{ transactions: Transaction[] }>("/me/points/history?page=1&limit=5"),
    ]);
    setSummary(points);
    setActivity(history.transactions ?? []);
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const session = await api<{ authentifie?: boolean; profil?: Profile }>("/auth/session");
        if (!alive || session.authentifie !== true || !session.profil || session.profil.role !== "VIEWER") {
          window.location.replace("/connexion");
          return;
        }
        setProfile(session.profil);
        try {
          await api("/me/daily-checkin", { method: "POST" });
        } catch (checkinError) {
          if (!(checkinError instanceof Error && checkinError.message === "HTTP 409")) throw checkinError;
        }
        if (alive) await refresh();
      } catch {
        if (alive) setError("Impossible de charger ton espace. Vérifie ta connexion puis réessaie.");
      }
    })();
    return () => { alive = false; };
  }, [refresh]);

  useEffect(() => {
    if (!modal) return;
    modalClose.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setModal(null); requestAnimationFrame(() => modalTrigger.current?.focus()); }
      if (event.key === "Tab") {
        const items = Array.from(document.querySelectorAll<HTMLElement>("[data-dashboard-modal] button, [data-dashboard-modal] a"));
        if (event.shiftKey && document.activeElement === items[0]) { event.preventDefault(); items.at(-1)?.focus(); }
        else if (!event.shiftKey && document.activeElement === items.at(-1)) { event.preventDefault(); items[0]?.focus(); }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [modal]);

  const closeModal = () => {
    setModal(null);
    requestAnimationFrame(() => modalTrigger.current?.focus());
  };
  const openHistory = async (event: React.MouseEvent<HTMLButtonElement>) => {
    modalTrigger.current = event.currentTarget;
    setModal("history");
    setHistoryLoading(true);
    try {
      const first = await api<{ transactions: Transaction[]; totalPages?: number }>("/me/points/history?page=1&limit=100");
      const pages = await Promise.all(Array.from({ length: Math.max(0, (first.totalPages ?? 1) - 1) }, (_, index) =>
        api<{ transactions: Transaction[] }>(`/me/points/history?page=${index + 2}&limit=100`),
      ));
      setFullHistory([...(first.transactions ?? []), ...pages.flatMap((page) => page.transactions ?? [])]);
    } catch {
      setFullHistory([]);
    } finally { setHistoryLoading(false); }
  };
  const transactionTitle = (item: Transaction) => transactionLabels[item.type] ?? "Mouvement de points";
  const transactionDate = (item: Transaction) => item.createdAt;

  const classic = summary?.ticketsDisponibles.CLASSIC ?? 0;
  const premium = summary?.ticketsDisponibles.PREMIUM ?? 0;
  return (
    <DashboardShell role="VIEWER" profileName={profile?.pseudo} modalOpen={modal !== null} onAccountClick={(event) => { modalTrigger.current = event.currentTarget; setModal("account"); }}>
      <div className="vd-content">
        <section className="vd-welcome" aria-labelledby="vd-title"><div><p className="vd-eyebrow">TON ESPACE PERSONNEL</p><h1 id="vd-title">Bonjour{profile?.pseudo ? `, ${profile.pseudo}` : ""} <span aria-hidden="true">✦</span></h1><p className="vd-subtitle">Chaque jour compte. Continue sur ta lancée !</p></div><div className="vd-date"><span className="vd-date-icon" aria-hidden="true">◷</span><span>Ta progression<br /><strong>en un coup d’œil</strong></span></div></section>
        {error && <p className="vd-error" role="alert">{error}</p>}
        <section className="vd-stats" aria-label="Résumé de progression">
          <article className="vd-card vd-points"><div className="vd-card-label"><span className="vd-icon vd-icon-violet">✦</span><span>Solde de points</span></div><div className="vd-number">{summary?.soldePoints ?? "—"}<small> pts</small></div><p className="vd-card-foot">Tes points cumulés</p><div className="vd-orbit" aria-hidden="true">✦</div></article>
          <article className="vd-card vd-streak"><div className="vd-card-label"><span className="vd-icon vd-icon-cyan">♨</span><span>Série actuelle</span></div><div className="vd-number">{summary?.streakActuel ?? "—"}<small> jours</small></div><p className="vd-card-foot">Record personnel : <strong>{summary?.streakMax ?? "—"} jours</strong></p><div className="vd-streak-track"><i /><i /><i /><i /><i /><i /><i /></div></article>
          <article className="vd-card vd-tickets"><div className="vd-card-label"><span className="vd-icon vd-icon-gold">♧</span><span>Tickets disponibles</span></div><div className="vd-ticket-counts"><div><strong>{classic}</strong><span>CLASSIC</span></div><b aria-hidden="true">·</b><div><strong>{premium}</strong><span>PREMIUM</span></div></div><p className="vd-card-foot">À utiliser dans tes tirages</p><div className="vd-ticket-art" aria-hidden="true">✧</div></article>
        </section>
        <section className="vd-lower">
          <article className="vd-panel vd-progress"><div className="vd-panel-heading"><div><p className="vd-eyebrow">RÉGULARITÉ RÉCOMPENSÉE</p><h2>Ta progression</h2></div><span className="vd-flame" aria-hidden="true">♨</span></div><div className="vd-progress-copy"><div><strong>{summary?.streakActuel ?? 0} <small>jours de suite</small></strong><span>Prochain palier : <b>{summary?.prochainPalierStreak ?? "—"} jours</b></span></div><span className="vd-next">✦</span></div><div className="vd-progress-line"><span style={{ width: `${summary?.prochainPalierStreak ? Math.min(100, ((summary.streakActuel ?? 0) / summary.prochainPalierStreak) * 100) : 0}%` }} /></div><p className="vd-milestone">Reviens chaque jour pour débloquer des tickets bonus.</p></article>
          <article className="vd-panel vd-activity"><div className="vd-panel-heading"><div><p className="vd-eyebrow">TON HISTORIQUE</p><h2>Activité récente</h2></div><button className="vd-text-button" onClick={openHistory}>Tout voir <span aria-hidden="true">↗</span></button></div>{activity.length ? <ul className="vd-activity-list">{activity.slice(0, 3).map((item) => <li key={item.id}><span className="vd-activity-mark">✦</span><span className="vd-activity-desc"><strong>{transactionTitle(item)}</strong><small>{transactionDate(item) ? new Date(transactionDate(item)!).toLocaleDateString("fr-FR", { day: "numeric", month: "short" }) : ""}</small></span><b className={item.montant >= 0 ? "positive" : "negative"}>{item.montant > 0 ? "+" : ""}{item.montant} pts</b></li>)}</ul> : <p className="vd-empty">Tes prochaines activités apparaîtront ici.</p>}</article>
        </section>
        <footer className="vd-footer"><span>Fais de chaque jour une occasion de gagner.</span><span>SKKUP <i>•</i> TON UNIVERS, TES RÈGLES</span></footer>
      </div>
      {modal && typeof document !== "undefined" && createPortal(<div className="vd-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) closeModal(); }}><section className="vd-modal" role="dialog" aria-modal="true" aria-labelledby="vd-modal-title" data-dashboard-modal><button ref={modalClose} className="vd-modal-close" onClick={closeModal} aria-label="Fermer">×</button>{modal === "account" ? <><p className="vd-eyebrow">ESPACE PERSONNEL</p><h2 id="vd-modal-title">Mon compte</h2><div className="vd-profile-line"><span className="vd-avatar">{profile?.pseudo.slice(0, 1).toUpperCase()}</span><div><strong>{profile?.pseudo}</strong><span>{profile?.email}</span></div></div><button className="vd-modal-secondary" onClick={async () => { try { await api("/auth/logout", { method: "POST" }); } finally { window.location.assign("/connexion"); } }}>Se déconnecter</button></> : <><p className="vd-eyebrow">TES POINTS</p><h2 id="vd-modal-title">Historique complet</h2><div className="vd-history-list">{historyLoading ? <p className="vd-empty">Chargement de ton historique…</p> : fullHistory?.length ? fullHistory.map((item) => <div key={item.id}><span><strong>{transactionTitle(item)}</strong><small>{transactionDate(item) ? new Date(transactionDate(item)!).toLocaleString("fr-FR") : ""}</small></span><b className={item.montant >= 0 ? "positive" : "negative"}>{item.montant > 0 ? "+" : ""}{item.montant} pts</b></div>) : <p className="vd-empty">Aucune transaction pour le moment.</p>}</div></>}</section></div>, document.body)}
    </DashboardShell>
  );
}
