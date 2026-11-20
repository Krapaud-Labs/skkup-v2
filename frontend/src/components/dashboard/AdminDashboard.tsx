"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { AdminRaffleManager } from "@/components/dashboard/AdminRaffleManager";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Profile = Readonly<{ id: string; pseudo: string; email: string }>;
type User = Readonly<{
  id: string;
  pseudo: string;
  email: string;
  role: string;
  actif: boolean;
  soldePoints: number;
  streakActuel: number;
  createdAt: string;
  _count: { raffleTickets: number | null; watchSessions: number | null };
}>;
type UserDetails = User & Readonly<{
  streakMax: number;
  derniereVisiteAt: string | null;
  _count: User["_count"] & { pointsTransactions: number };
}>;
type AuditEvent = Readonly<{
  id: string;
  action: string;
  metadata: Record<string, unknown> | null;
  actorId: string;
  createdAt: string;
}>;
type AdminActivity = Readonly<{
  id: string;
  action: string;
  entityType: string;
  entityId: string;
  createdAt: string;
  actor: Readonly<{ id: string; pseudo: string }>;
}>;
type SummaryAnnouncement = Readonly<{
  id: string;
  titre: string;
  texte: string;
  status: string;
  actif: boolean;
  debutAt: string | null;
  finAt: string | null;
}>;
type SummaryContent = Readonly<{
  id: string;
  slug: string;
  locale: string;
  status: string;
  version: number;
}>;
type AdminSummary = Readonly<{
  availability: Readonly<Record<string, "available" | "not_implemented">>;
  counts: Readonly<{
    users: number;
    activeUsers: number;
    openRaffles: number | null;
    totalRaffles: number | null;
    availableLots: number | null;
    totalLots: number | null;
    publishedContent: number;
    activeAnnouncements: number;
    totalAnnouncements: number;
    openFraudFlags: number | null;
    totalFraudFlags: number | null;
    activeStreams: number | null;
  }>;
  recentActivity: AdminActivity[];
  raffles: unknown[] | null;
  lots: unknown[] | null;
  announcements: SummaryAnnouncement[] | null;
  fraudFlags: unknown[] | null;
  contents: SummaryContent[] | null;
}>;
type SummarySelection =
  | Readonly<{ kind: "activity"; value: AdminActivity }>
  | Readonly<{ kind: "announcement"; value: SummaryAnnouncement }>
  | Readonly<{ kind: "content"; value: SummaryContent }>;
type GlobalAuditItem = Readonly<{
  id: string;
  action: string;
  entityType: string;
  entityId: string;
  createdAt: string;
  actor: Readonly<{ id: string; pseudo: string }>;
}>;
type GlobalAuditPage = Readonly<{ items: GlobalAuditItem[]; total: number; page: number; limit: number }>;
type FlagStatus = "OUVERTE" | "EXAMINEE" | "IGNOREE";
type ModerationFlag = Readonly<{
  id: string;
  userId: string;
  statut: FlagStatus;
  createdAt: string;
  examineeAt: string | null;
  user: Readonly<{ id: string; pseudo: string }>;
}>;
type ModerationAvailability = Readonly<{ sourceDetails: "not_implemented"; watchSession: "not_implemented" }>;
type ModerationAudit = Readonly<{ id: string; action: string; actor: Readonly<{ id: string; pseudo: string }>; createdAt: string }>;
type ModerationFlagDetails = ModerationFlag & Readonly<{ audit: ModerationAudit[]; availability: ModerationAvailability }>;
type ModerationPage = Readonly<{ items: ModerationFlag[]; total: number; page: number; limit: number; availability: ModerationAvailability }>;
type ModerationFilter = "TOUTES" | FlagStatus;
type Dialog = "account" | "details" | "audit" | "summary-item" | "global-audit" | "moderation" | null;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    credentials: "include",
    headers: { ...(init?.headers ?? {}), ...(init?.body ? { "Content-Type": "application/json" } : {}) },
  });
  if (response.status === 401) {
    window.location.replace("/connexion");
    throw new Error("Session expirée. Reconnecte-toi.");
  }
  if (response.status === 403) throw new Error("Accès administrateur requis.");
  if (!response.ok) {
    let message = "Une erreur est survenue. Réessaie.";
    try {
      const body = await response.json() as { detail?: string };
      if (typeof body.detail === "string") message = body.detail;
    } catch { /* Keep the safe fallback message. */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function dateLabel(value: string | null | undefined, withTime = false) {
  if (!value) return "Jamais";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date inconnue";
  return new Intl.DateTimeFormat("fr-FR", withTime
    ? { dateStyle: "medium", timeStyle: "short" }
    : { dateStyle: "medium" }).format(date);
}

function actionLabel(action: string) {
  const labels: Record<string, string> = {
    USER_ACTIVATED: "Compte activé",
    USER_DEACTIVATED: "Compte désactivé",
  };
  return labels[action] ?? "Action d’administration";
}

function activityLabel(action: string) {
  const labels: Record<string, string> = {
    USER_ACTIVATED: "Compte activé",
    USER_DEACTIVATED: "Compte désactivé",
    ANNOUNCEMENT_CREATED: "Annonce créée",
    ANNOUNCEMENT_UPDATED: "Annonce modifiée",
    ANNOUNCEMENT_PUBLISHED: "Annonce publiée",
    ANNOUNCEMENT_ARCHIVED: "Annonce archivée",
    CONTENT_CREATED: "Contenu créé",
    CONTENT_UPDATED: "Contenu modifié",
    CONTENT_PUBLISHED: "Contenu publié",
  };
  return labels[action] ?? "Opération d’administration";
}

function countLabel(value: number | null | undefined) {
  return value === null || value === undefined ? "Indisponible" : value.toLocaleString("fr-FR");
}

function statusLabel(status: string) {
  const labels: Record<string, string> = { DRAFT: "Brouillon", PUBLISHED: "Publié", ARCHIVED: "Archivé" };
  return labels[status] ?? "Statut inconnu";
}

function flagStatusLabel(status: FlagStatus) {
  const labels: Record<FlagStatus, string> = { OUVERTE: "Ouverte", EXAMINEE: "Examinée", IGNOREE: "Ignorée" };
  return labels[status];
}

function availabilityText(value: string) {
  if (value === "not_implemented") return "Non implémenté";
  if (value === "available") return "Disponible";
  return "Indisponible";
}

export function AdminDashboard({ profile }: Readonly<{ profile: Profile }>) {
  const [section, setSection] = useState<"overview" | "users">("overview");
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");
  const [summarySelection, setSummarySelection] = useState<SummarySelection | null>(null);
  const [globalAudit, setGlobalAudit] = useState<GlobalAuditItem[]>([]);
  const [globalAuditTotal, setGlobalAuditTotal] = useState(0);
  const [globalAuditPage, setGlobalAuditPage] = useState(1);
  const [globalAuditLoading, setGlobalAuditLoading] = useState(false);
  const [globalAuditError, setGlobalAuditError] = useState("");
  const [globalAuditSelected, setGlobalAuditSelected] = useState<GlobalAuditItem | null>(null);
  const [globalAuditRefresh, setGlobalAuditRefresh] = useState(0);
  const [moderationItems, setModerationItems] = useState<ModerationFlag[]>([]);
  const [moderationTotal, setModerationTotal] = useState(0);
  const [moderationPage, setModerationPage] = useState(1);
  const [moderationFilter, setModerationFilter] = useState<ModerationFilter>("TOUTES");
  const [moderationLoading, setModerationLoading] = useState(false);
  const [moderationError, setModerationError] = useState("");
  const [moderationRefresh, setModerationRefresh] = useState(0);
  const [moderationView, setModerationView] = useState<"list" | "detail">("list");
  const [selectedFlag, setSelectedFlag] = useState<ModerationFlagDetails | null>(null);
  const [selectedFlagLoading, setSelectedFlagLoading] = useState(false);
  const [selectedFlagError, setSelectedFlagError] = useState("");
  const [moderationStatus, setModerationStatus] = useState<FlagStatus>("OUVERTE");
  const [moderationNote, setModerationNote] = useState("");
  const [savingModeration, setSavingModeration] = useState(false);
  const [moderationNotice, setModerationNotice] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);
  const [rafflesOpen, setRafflesOpen] = useState(false);
  const [selected, setSelected] = useState<UserDetails | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [dialogLoading, setDialogLoading] = useState(false);
  const [savingStatus, setSavingStatus] = useState(false);
  const [notice, setNotice] = useState("");
  const [dialogError, setDialogError] = useState("");
  const [confirmStatus, setConfirmStatus] = useState(false);
  const loadVersion = useRef(0);
  const previousSearch = useRef("");
  const previousRafflesOpen = useRef(false);
  const returnTrigger = useRef<HTMLElement | null>(null);
  const raffleTrigger = useRef<HTMLButtonElement>(null);
  const globalAuditTrigger = useRef<HTMLElement | null>(null);
  const moderationItemTrigger = useRef<HTMLElement | null>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (previousRafflesOpen.current && !rafflesOpen) {
      requestAnimationFrame(() => {
        if (raffleTrigger.current?.isConnected) raffleTrigger.current.focus({ preventScroll: true });
      });
    }
    previousRafflesOpen.current = rafflesOpen;
  }, [rafflesOpen]);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError("");
    try { setSummary(await request<AdminSummary>("/admin/dashboard/summary")); }
    catch (loadError) { setSummaryError(loadError instanceof Error ? loadError.message : "Impossible de charger le cockpit Admin."); }
    finally { setSummaryLoading(false); }
  }, []);

  useEffect(() => { void loadSummary(); }, [loadSummary]);

  const loadUsers = useCallback(async (term: string, showSpinner = true) => {
    const version = ++loadVersion.current;
    if (showSpinner) setLoading(true);
    setError("");
    try {
      const query = term.trim() ? `?search=${encodeURIComponent(term.trim())}` : "";
      const result = await request<User[]>(`/admin/users${query}`);
      if (version === loadVersion.current) setUsers(result);
    } catch (loadError) {
      if (version === loadVersion.current) setError(loadError instanceof Error ? loadError.message : "Impossible de charger les utilisateurs.");
    } finally { if (version === loadVersion.current) setLoading(false); }
  }, []);

  useEffect(() => { if (section === "users") void loadUsers(search); }, [loadUsers, section]);

  useEffect(() => {
    if (section !== "users") return;
    if (previousSearch.current === search) return;
    previousSearch.current = search;
    if (!search.trim()) {
      const timer = window.setTimeout(() => void loadUsers("", false), 160);
      return () => window.clearTimeout(timer);
    }
    const timer = window.setTimeout(() => void loadUsers(search, false), 250);
    return () => window.clearTimeout(timer);
  }, [loadUsers, search, section]);

  useEffect(() => {
    if (!dialog) return;
    closeButton.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); closeDialog(); }
      if (event.key !== "Tab") return;
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])',
      );
      if (!focusable?.length) { event.preventDefault(); dialogRef.current?.focus(); return; }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [dialog]);

  useEffect(() => {
    if (dialog !== "global-audit") return;
    let active = true;
    setGlobalAuditLoading(true);
    setGlobalAuditError("");
    request<GlobalAuditPage>(`/admin/audit?page=${globalAuditPage}&limit=20`)
      .then((result) => {
        if (!active) return;
        setGlobalAudit(result.items);
        setGlobalAuditTotal(result.total);
      })
      .catch((loadError) => {
        if (active) setGlobalAuditError(loadError instanceof Error ? loadError.message : "Impossible de charger le journal global.");
      })
      .finally(() => { if (active) setGlobalAuditLoading(false); });
    return () => { active = false; };
  }, [dialog, globalAuditPage, globalAuditRefresh]);

  useEffect(() => {
    if (dialog !== "moderation" || moderationView !== "list") return;
    let active = true;
    setModerationLoading(true);
    setModerationError("");
    const query = new URLSearchParams({ page: String(moderationPage), limit: "20" });
    if (moderationFilter !== "TOUTES") query.set("statut", moderationFilter);
    request<ModerationPage>(`/admin/fraud/flags?${query.toString()}`)
      .then((result) => {
        if (!active) return;
        setModerationItems(result.items);
        setModerationTotal(result.total);
      })
      .catch((loadError) => {
        if (active) setModerationError(loadError instanceof Error ? loadError.message : "Impossible de charger les signalements.");
      })
      .finally(() => { if (active) setModerationLoading(false); });
    return () => { active = false; };
  }, [dialog, moderationView, moderationPage, moderationFilter, moderationRefresh]);

  const closeDialog = () => {
    setDialog(null);
    setDialogError("");
    setConfirmStatus(false);
    requestAnimationFrame(() => returnTrigger.current?.focus());
  };

  const openDetails = async (user: User, trigger: HTMLElement) => {
    returnTrigger.current = trigger;
    setSelected(null);
    setAudit([]);
    setDialogError("");
    setDialogLoading(true);
    setDialog("details");
    try {
      setSelected(await request<UserDetails>(`/admin/users/${encodeURIComponent(user.id)}`));
    } catch (loadError) {
      setDialogError(loadError instanceof Error ? loadError.message : "Impossible de charger ce compte.");
    } finally { setDialogLoading(false); }
  };

  const showAudit = async () => {
    setAudit([]);
    setDialogError("");
    setConfirmStatus(false);
    setDialogLoading(true);
    setDialog("audit");
    try {
      if (!selected) throw new Error("Le compte n’est plus sélectionné.");
      setAudit(await request<AuditEvent[]>(`/admin/users/${encodeURIComponent(selected.id)}/audit`));
    } catch (loadError) {
      setDialogError(loadError instanceof Error ? loadError.message : "Impossible de charger le journal.");
    } finally { setDialogLoading(false); }
  };

  const openSummarySelection = (selection: SummarySelection, trigger: HTMLElement) => {
    returnTrigger.current = trigger;
    setSummarySelection(selection);
    setDialog("summary-item");
  };

  const openModeration = (trigger: HTMLElement) => {
    returnTrigger.current = trigger;
    setModerationView("list");
    setSelectedFlag(null);
    setModerationPage(1);
    setModerationFilter("TOUTES");
    setModerationError("");
    setDialog("moderation");
  };

  const openFlagDetails = async (item: ModerationFlag, trigger: HTMLElement) => {
    moderationItemTrigger.current = trigger;
    setModerationView("detail");
    setSelectedFlag(null);
    setSelectedFlagError("");
    setSelectedFlagLoading(true);
    setModerationNote("");
    try {
      const details = await request<ModerationFlagDetails>(`/admin/fraud/flags/${encodeURIComponent(item.id)}`);
      setSelectedFlag(details);
      setModerationStatus(details.statut);
    } catch (loadError) {
      setSelectedFlagError(loadError instanceof Error ? loadError.message : "Impossible de charger ce signalement.");
    } finally { setSelectedFlagLoading(false); }
  };

  const saveModeration = async () => {
    if (!selectedFlag) return;
    setSavingModeration(true);
    setSelectedFlagError("");
    setModerationNotice("");
    const note = moderationNote.trim();
    try {
      await request<unknown>(`/admin/fraud/flags/${encodeURIComponent(selectedFlag.id)}`, {
        method: "PATCH",
        body: JSON.stringify({ statut: moderationStatus, ...(note ? { note } : {}) }),
      });
      setSelectedFlag((current) => current ? { ...current, statut: moderationStatus } : current);
      setModerationNote("");
      setModerationNotice("Le traitement du signalement a été enregistré.");
      setModerationRefresh((value) => value + 1);
      try {
        const updated = await request<ModerationFlagDetails>(`/admin/fraud/flags/${encodeURIComponent(selectedFlag.id)}`);
        setSelectedFlag(updated);
        setModerationStatus(updated.statut);
      } catch { /* The successful PATCH remains reflected; a later reopen reloads audit details. */ }
    } catch (saveError) {
      setSelectedFlagError(saveError instanceof Error ? saveError.message : "Impossible d’enregistrer ce traitement.");
    } finally { setSavingModeration(false); }
  };

  const updateStatus = async () => {
    if (!selected || (selected.id === profile.id && selected.actif)) return;
    setConfirmStatus(false);
    setSavingStatus(true);
    setDialogError("");
    try {
      const updated = await request<Pick<UserDetails, "id" | "pseudo" | "role" | "actif">>(
        `/admin/users/${encodeURIComponent(selected.id)}/status`,
        { method: "PATCH", body: JSON.stringify({ actif: !selected.actif }) },
      );
      setSelected((current) => current ? { ...current, actif: updated.actif } : current);
      setUsers((current) => current.map((user) => user.id === updated.id ? { ...user, actif: updated.actif } : user));
      setNotice(updated.actif ? `${updated.pseudo} a été activé.` : `${updated.pseudo} a été désactivé.`);
      setTimeout(() => setNotice(""), 4500);
    } catch (updateError) {
      setDialogError(updateError instanceof Error ? updateError.message : "Impossible de modifier le statut.");
    } finally { setSavingStatus(false); }
  };

  return (
    <DashboardShell role="ADMIN" profileName={profile.pseudo} modalOpen={dialog !== null || rafflesOpen} onAccountClick={(event) => {
      returnTrigger.current = event.currentTarget;
      setDialog("account");
    }}>
      <div className="vd-content admin-dashboard">
        <section className="vd-welcome admin-welcome" aria-labelledby="admin-title">
          <div>
            <p className="vd-eyebrow">ESPACE D’ADMINISTRATION</p>
            <h1 id="admin-title">Bonjour, {profile.pseudo} <span aria-hidden="true">✦</span></h1>
            <p className="vd-subtitle">Le pilotage Skkup, dans une vue claire et centralisée.</p>
          </div>
          <div className="admin-session-badge"><i aria-hidden="true" /> Session administrateur</div>
        </section>

        <nav className="admin-section-nav" aria-label="Sections du tableau de bord Admin">
          <button type="button" aria-pressed={section === "overview"} className={section === "overview" ? "is-current" : ""} onClick={() => setSection("overview")}>Vue d’ensemble</button>
          <button type="button" aria-pressed={section === "users"} className={section === "users" ? "is-current" : ""} onClick={() => setSection("users")}>Utilisateurs</button>
          <button ref={raffleTrigger} type="button" aria-haspopup="dialog" onClick={() => setRafflesOpen(true)}>Tirages & lots</button>
          <button type="button" aria-haspopup="dialog" onClick={(event) => openModeration(event.currentTarget)}>Modération</button>
          <button type="button" aria-haspopup="dialog" onClick={(event) => {
            returnTrigger.current = event.currentTarget;
            setGlobalAuditSelected(null);
            setGlobalAuditPage(1);
            setDialog("global-audit");
          }}>Journal d’audit</button>
        </nav>

        {section === "overview" ? <section className="admin-cockpit" aria-labelledby="admin-cockpit-title">
          {summaryError ? <div className="admin-state admin-state-error" role="alert"><span>{summaryError}</span><button className="vd-text-button" onClick={() => void loadSummary()}>Réessayer</button></div> : summaryLoading || !summary ? <p className="admin-state" role="status">Chargement du cockpit…</p> : <>
            <header className="admin-cockpit-heading"><div><p className="vd-eyebrow">VUE D’ENSEMBLE</p><h2 id="admin-cockpit-title">Les repères essentiels</h2></div><button className="vd-text-button" onClick={() => setSection("users")}>Gérer les comptes <span aria-hidden="true">↗</span></button></header>
            <div className="admin-kpi-row">
              <button className="admin-kpi admin-kpi-featured" onClick={() => setSection("users")}><span>Comptes</span><strong>{countLabel(summary.counts.users)}</strong><small>{countLabel(summary.counts.activeUsers)} actifs</small></button>
              <article className="admin-kpi"><span>Annonces actives</span><strong>{countLabel(summary.counts.activeAnnouncements)}</strong><small>sur {countLabel(summary.counts.totalAnnouncements)} annonces</small></article>
              <article className="admin-kpi"><span>Contenus publiés</span><strong>{countLabel(summary.counts.publishedContent)}</strong><small>Versions publiées</small></article>
            </div>
            <div className="admin-cockpit-lower">
              <section className="admin-compact-panel" aria-labelledby="admin-activity-title">
                <header><div><p className="vd-eyebrow">JOURNAL</p><h3 id="admin-activity-title">Activité récente</h3></div><span className="admin-panel-icon" aria-hidden="true">✧</span></header>
                {summary.recentActivity.length ? <div className="admin-compact-list">{summary.recentActivity.slice(0, 3).map((item) => <button key={item.id} onClick={(event) => openSummarySelection({ kind: "activity", value: item }, event.currentTarget)} aria-haspopup="dialog"><span className="admin-activity-mark" aria-hidden="true">✦</span><span><strong>{activityLabel(item.action)}</strong><small>{item.actor.pseudo} · {dateLabel(item.createdAt, true)}</small></span><i aria-hidden="true">›</i></button>)}</div> : <p className="admin-compact-empty">Aucune activité récente à afficher.</p>}
              </section>
              <section className="admin-compact-panel" aria-labelledby="admin-publications-title">
                <header><div><p className="vd-eyebrow">PUBLICATIONS</p><h3 id="admin-publications-title">Contenus suivis</h3></div><span className="admin-panel-icon" aria-hidden="true">◈</span></header>
                {((summary.announcements ?? []).length + (summary.contents ?? []).length) ? <div className="admin-compact-list">{[...(summary.announcements ?? []).slice(0, 2).map((item) => ({ kind: "announcement" as const, value: item })), ...(summary.contents ?? []).slice(0, 2).map((item) => ({ kind: "content" as const, value: item }))].slice(0, 3).map((entry) => <button key={`${entry.kind}-${entry.value.id}`} onClick={(event) => openSummarySelection(entry, event.currentTarget)} aria-haspopup="dialog"><span className={`admin-publication-mark ${entry.kind}`} aria-hidden="true">{entry.kind === "announcement" ? "✧" : "▤"}</span><span><strong>{entry.kind === "announcement" ? entry.value.titre : entry.value.slug}</strong><small>{entry.kind === "announcement" ? statusLabel(entry.value.status) : `${entry.value.locale.toUpperCase()} · ${statusLabel(entry.value.status)}`}</small></span><i aria-hidden="true">›</i></button>)}</div> : <p className="admin-compact-empty">Aucune publication récente à afficher.</p>}
              </section>
            </div>
            <div className="admin-domain-status" aria-label="Disponibilité des domaines"><span>Domaines disponibles et à venir</span>{[["Raffles", "available"], ["Lots", "available"], ["Antifraude", summary.availability.fraudFlags], ["Streams", summary.availability.streams]].map(([name, value]) => <span className="admin-domain-chip" key={name}><i aria-hidden="true" />{name}: {value === "available" ? "Disponible" : "À venir"}</span>)}</div>
          </>}
        </section> : <section className="admin-users-panel" aria-labelledby="admin-users-title">
          <header className="admin-users-heading">
            <div><p className="vd-eyebrow">COMPTES & ACCÈS</p><h2 id="admin-users-title">Utilisateurs</h2></div>
            <span className="admin-user-total">{loading ? "…" : users.length === 100 ? "100 derniers" : `${users.length} comptes`}</span>
          </header>
          <label className="admin-search"><span aria-hidden="true">⌕</span><span className="sr-only">Rechercher un utilisateur</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Rechercher par pseudo ou email" type="search" /></label>
          {notice && <p className="admin-notice" role="status">{notice}</p>}
          {error ? <div className="admin-state admin-state-error" role="alert"><span>{error}</span><button className="vd-text-button" onClick={() => void loadUsers(search)}>Réessayer</button></div> : loading ? <p className="admin-state" role="status">Chargement des comptes…</p> : users.length === 0 ? <p className="admin-state">Aucun compte ne correspond à cette recherche.</p> : (
            <div className="admin-user-list" aria-label="Liste des utilisateurs">
              {users.map((user) => (
                <button className="admin-user-row" key={user.id} onClick={(event) => void openDetails(user, event.currentTarget)} aria-haspopup="dialog">
                  <span className="vd-avatar admin-user-avatar">{user.pseudo.slice(0, 1).toUpperCase()}</span>
                  <span className="admin-user-identity"><strong>{user.pseudo}</strong><small>{user.email}</small></span>
                  <span className={`admin-user-status ${user.actif ? "is-active" : "is-inactive"}`}><i aria-hidden="true" />{user.actif ? "Actif" : "Désactivé"}</span>
                  <span className="admin-user-points">{user.soldePoints.toLocaleString("fr-FR")} <small>pts</small></span>
                  <span className="admin-user-chevron" aria-hidden="true">›</span>
                </button>
              ))}
            </div>
          )}
          <p className="admin-scope-note">Jusqu’aux 100 comptes les plus récents sont affichés. Les compteurs de tirages et de visionnage ne sont pas encore disponibles en V2.</p>
        </section>}
        <footer className="vd-footer"><span>Une gestion claire, avec des accès contrôlés.</span><span>SKKUP <i>•</i> ADMINISTRATION</span></footer>
      </div>

      {dialog && typeof document !== "undefined" && createPortal(
        <div className="vd-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) closeDialog(); }}>
          <section className="vd-modal admin-modal" ref={dialogRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="admin-dialog-title" data-dashboard-modal>
            <button ref={closeButton} className="vd-modal-close" onClick={closeDialog} aria-label="Fermer">×</button>
            {dialog === "account" ? <>
              <p className="vd-eyebrow">ESPACE ADMINISTRATEUR</p><h2 id="admin-dialog-title">Mon compte</h2>
              <div className="vd-profile-line"><span className="vd-avatar">{profile.pseudo.slice(0, 1).toUpperCase()}</span><div><strong>{profile.pseudo}</strong><span>{profile.email}</span></div></div>
              <button className="vd-modal-secondary" onClick={async () => { try { await request("/auth/logout", { method: "POST" }); } finally { window.location.assign("/connexion"); } }}>Se déconnecter</button>
            </> : dialog === "moderation" ? <>
              <p className="vd-eyebrow">SÉCURITÉ & SIGNALEMENTS</p>
              <h2 id="admin-dialog-title">{moderationView === "list" ? "Modération" : "Traitement du signalement"}</h2>
              {moderationView === "list" ? <>
                <label className="admin-moderation-filter" htmlFor="moderation-filter"><span>Statut</span><select id="moderation-filter" value={moderationFilter} onChange={(event) => { setModerationFilter(event.target.value as ModerationFilter); setModerationPage(1); }}><option value="TOUTES">Tous les signalements</option><option value="OUVERTE">Ouverts</option><option value="EXAMINEE">Examinés</option><option value="IGNOREE">Ignorés</option></select></label>
                {moderationError ? <div className="admin-state admin-state-error" role="alert"><span>{moderationError}</span><button className="vd-text-button" onClick={() => setModerationRefresh((value) => value + 1)}>Réessayer</button></div> : moderationLoading ? <p className="vd-empty" role="status">Chargement des signalements…</p> : <>
                  <p className="admin-global-audit-total">{moderationTotal.toLocaleString("fr-FR")} signalements · {moderationItems.length ? `page ${moderationPage}` : "aucun résultat"}</p>
                  {moderationItems.length ? <div className="admin-global-audit-list">{moderationItems.map((item) => <button className="admin-global-audit-entry admin-flag-entry" key={item.id} onClick={(event) => void openFlagDetails(item, event.currentTarget)} aria-haspopup="dialog"><span className={`admin-flag-dot ${item.statut.toLowerCase()}`} aria-hidden="true" /><span><strong>{item.user.pseudo}</strong><small>{flagStatusLabel(item.statut)} · {dateLabel(item.createdAt, true)}</small></span><i aria-hidden="true">›</i></button>)}</div> : <p className="vd-empty">Aucun signalement trouvé.</p>}
                  <div className="admin-audit-pagination"><button className="admin-confirm-cancel" onClick={() => setModerationPage((page) => Math.max(1, page - 1))} disabled={moderationPage <= 1 || moderationLoading}>Précédent</button><span>Page {moderationPage} / {Math.max(1, Math.ceil(moderationTotal / 20))}</span><button className="admin-confirm-cancel" onClick={() => setModerationPage((page) => Math.min(Math.ceil(moderationTotal / 20), page + 1))} disabled={moderationPage * 20 >= moderationTotal || moderationLoading}>Suivant</button></div>
                </>}
              </> : <>
                <div className="admin-modal-actions"><button className="vd-text-button" onClick={() => { setModerationView("list"); setSelectedFlag(null); requestAnimationFrame(() => dialogRef.current?.querySelector<HTMLElement>("#moderation-filter")?.focus()); }}>← Retour aux signalements</button></div>
                {selectedFlagLoading ? <p className="vd-empty" role="status">Chargement du signalement…</p> : selectedFlagError ? <p className="admin-dialog-error" role="alert">{selectedFlagError}</p> : selectedFlag && <>
                  <div className="admin-summary-detail">
                    <div><span>Compte concerné</span><strong>{selectedFlag.user.pseudo}</strong></div>
                    <div><span>Statut actuel</span><strong>{flagStatusLabel(selectedFlag.statut)}</strong></div>
                    <div><span>Signalé le</span><strong>{dateLabel(selectedFlag.createdAt, true)}</strong></div>
                    <div><span>Examiné le</span><strong>{selectedFlag.examineeAt ? dateLabel(selectedFlag.examineeAt, true) : "Aucune date enregistrée"}</strong></div>
                  </div>
                  <div className="admin-availability-notes"><span>Source détaillée : {availabilityText(selectedFlag.availability.sourceDetails)}</span><span>Session de visionnage : {availabilityText(selectedFlag.availability.watchSession)}</span></div>
                  <section className="admin-flag-treatment" aria-labelledby="flag-treatment-title">
                    <h3 id="flag-treatment-title">Mettre à jour le traitement</h3>
                    <label htmlFor="flag-status">Statut</label><select id="flag-status" value={moderationStatus} onChange={(event) => setModerationStatus(event.target.value as FlagStatus)}><option value="OUVERTE">Ouverte</option><option value="EXAMINEE">Examinée</option><option value="IGNOREE">Ignorée</option></select>
                    <label htmlFor="flag-note">Note facultative</label><textarea id="flag-note" value={moderationNote} onChange={(event) => setModerationNote(event.target.value)} maxLength={2000} rows={3} placeholder="Ajouter une note à cette mise à jour" />
                    <div className="admin-note-count">{moderationNote.length} / 2000</div>
                    {selectedFlagError && <p className="admin-dialog-error" role="alert">{selectedFlagError}</p>}
                    {moderationNotice && <p className="admin-notice" role="status">{moderationNotice}</p>}
                    <button className="vd-modal-secondary admin-save-treatment" onClick={() => void saveModeration()} disabled={savingModeration}>{savingModeration ? "Enregistrement…" : "Enregistrer le traitement"}</button>
                  </section>
                  <section className="admin-flag-audit" aria-labelledby="flag-audit-title"><h3 id="flag-audit-title">Historique du signalement</h3>{selectedFlag.audit.length ? <div>{selectedFlag.audit.slice(0, 8).map((event) => <article key={event.id}><span className="admin-audit-dot" aria-hidden="true" /><span><strong>{activityLabel(event.action)}</strong><small>{event.actor.pseudo} · {dateLabel(event.createdAt, true)}</small></span></article>)}</div> : <p>Aucun événement enregistré.</p>}</section>
                </>}
              </>}
            </> : dialog === "global-audit" ? <>
              <p className="vd-eyebrow">TRAÇABILITÉ ADMIN</p>
              <h2 id="admin-dialog-title">{globalAuditSelected ? "Détail de l’événement" : "Journal d’audit"}</h2>
              {globalAuditSelected ? <>
                <div className="admin-modal-actions"><button className="vd-text-button" onClick={() => { setGlobalAuditSelected(null); requestAnimationFrame(() => globalAuditTrigger.current?.focus()); }}>← Retour au journal</button></div>
                <div className="admin-summary-detail">
                  <div><span>Action</span><strong>{actionLabel(globalAuditSelected.action)}</strong></div>
                  <div><span>Administrateur</span><strong>{globalAuditSelected.actor.pseudo}</strong></div>
                  <div><span>Type de cible</span><strong>{globalAuditSelected.entityType}</strong></div>
                  <div><span>Identifiant de cible</span><strong>{globalAuditSelected.entityId}</strong></div>
                  <div><span>Date</span><strong>{dateLabel(globalAuditSelected.createdAt, true)}</strong></div>
                </div>
              </> : globalAuditError ? <div className="admin-state admin-state-error" role="alert"><span>{globalAuditError}</span><button className="vd-text-button" onClick={() => setGlobalAuditRefresh((value) => value + 1)}>Réessayer</button></div> : globalAuditLoading ? <p className="vd-empty" role="status">Chargement du journal…</p> : <>
                <p className="admin-global-audit-total">{globalAuditTotal.toLocaleString("fr-FR")} événements · {globalAudit.length ? `page ${globalAuditPage}` : "aucun résultat"}</p>
                {globalAudit.length ? <div className="admin-global-audit-list">{globalAudit.map((item) => <button className="admin-global-audit-entry" key={item.id} onClick={(event) => { globalAuditTrigger.current = event.currentTarget; setGlobalAuditSelected(item); requestAnimationFrame(() => closeButton.current?.focus()); }} aria-haspopup="dialog"><span className="admin-audit-dot" aria-hidden="true" /><span><strong>{actionLabel(item.action)}</strong><small>{item.actor.pseudo} · {item.entityType} · {dateLabel(item.createdAt, true)}</small></span><i aria-hidden="true">›</i></button>)}</div> : <p className="vd-empty">Aucun événement d’administration enregistré.</p>}
                <div className="admin-audit-pagination"><button className="admin-confirm-cancel" onClick={() => setGlobalAuditPage((page) => Math.max(1, page - 1))} disabled={globalAuditPage <= 1 || globalAuditLoading}>Précédent</button><span>Page {globalAuditPage} / {Math.max(1, Math.ceil(globalAuditTotal / 20))}</span><button className="admin-confirm-cancel" onClick={() => setGlobalAuditPage((page) => Math.min(Math.ceil(globalAuditTotal / 20), page + 1))} disabled={globalAuditPage * 20 >= globalAuditTotal || globalAuditLoading}>Suivant</button></div>
              </>}
            </> : dialog === "summary-item" && summarySelection ? <>
              {summarySelection.kind === "activity" ? <>
                <p className="vd-eyebrow">JOURNAL D’ADMINISTRATION</p><h2 id="admin-dialog-title">{activityLabel(summarySelection.value.action)}</h2>
                <div className="admin-summary-detail"><div><span>Administrateur</span><strong>{summarySelection.value.actor.pseudo}</strong></div><div><span>Enregistrement</span><strong>{summarySelection.value.entityType} · {summarySelection.value.entityId}</strong></div><div><span>Date</span><strong>{dateLabel(summarySelection.value.createdAt, true)}</strong></div></div>
              </> : summarySelection.kind === "announcement" ? <>
                <p className="vd-eyebrow">ANNONCE</p><h2 id="admin-dialog-title">{summarySelection.value.titre}</h2>
                <div className="admin-summary-detail"><div><span>Statut</span><strong>{statusLabel(summarySelection.value.status)} · {summarySelection.value.actif ? "active" : "inactive"}</strong></div><div><span>Début</span><strong>{dateLabel(summarySelection.value.debutAt, true)}</strong></div><div><span>Fin</span><strong>{dateLabel(summarySelection.value.finAt, true)}</strong></div></div>
                <div className="admin-summary-copy">{summarySelection.value.texte}</div>
              </> : <>
                <p className="vd-eyebrow">CONTENU ÉDITORIAL</p><h2 id="admin-dialog-title">{summarySelection.value.slug}</h2>
                <div className="admin-summary-detail"><div><span>Langue</span><strong>{summarySelection.value.locale.toUpperCase()}</strong></div><div><span>Statut</span><strong>{statusLabel(summarySelection.value.status)}</strong></div><div><span>Version</span><strong>{summarySelection.value.version}</strong></div></div>
                <p className="admin-scope-note">Le résumé ne contient pas le corps du contenu. Son détail complet sera affiché quand l’API de consultation sera reliée à cette vue.</p>
              </>}
            </> : dialog === "audit" ? <>
              <p className="vd-eyebrow">TRAÇABILITÉ DU COMPTE</p><h2 id="admin-dialog-title">Journal · {selected?.pseudo}</h2>
              <div className="admin-modal-actions"><button className="vd-text-button" onClick={() => { setDialog("details"); setDialogError(""); }}>← Retour au compte</button></div>
              {dialogError ? <p className="admin-dialog-error" role="alert">{dialogError}</p> : dialogLoading ? <p className="vd-empty" role="status">Chargement du journal…</p> : audit.length ? <div className="admin-audit-list">{audit.map((event) => <article key={event.id}><span className="admin-audit-dot" aria-hidden="true" /><div><strong>{actionLabel(event.action)}</strong><small>{dateLabel(event.createdAt, true)} · Admin {event.actorId.slice(0, 8)}</small>{event.metadata && <p>{event.metadata.previousActif === false ? "Compte auparavant désactivé" : event.metadata.previousActif === true ? "Compte auparavant actif" : ""}{typeof event.metadata.actif === "boolean" ? ` · Nouveau statut : ${event.metadata.actif ? "actif" : "désactivé"}` : ""}</p>}</div></article>)}</div> : <p className="vd-empty">Aucun événement d’administration enregistré.</p>}
            </> : <>
              <p className="vd-eyebrow">GESTION DES COMPTES</p><h2 id="admin-dialog-title">{selected?.pseudo ?? "Détail du compte"}</h2>
              {dialogLoading ? <p className="vd-empty" role="status">Chargement du compte…</p> : selected && <>
                {dialogError && <p className="admin-dialog-error" role="alert">{dialogError}</p>}
                <div className="admin-detail-grid">
                  <div><span>Email</span><strong>{selected.email}</strong></div>
                  <div><span>Rôle</span><strong>{selected.role === "ADMIN" ? "Administrateur" : "Viewer"}</strong></div>
                  <div><span>Statut</span><strong className={selected.actif ? "admin-detail-active" : "admin-detail-inactive"}>{selected.actif ? "Actif" : "Désactivé"}</strong></div>
                  <div><span>Inscription</span><strong>{dateLabel(selected.createdAt)}</strong></div>
                  <div><span>Points</span><strong>{selected.soldePoints.toLocaleString("fr-FR")}</strong></div>
                  <div><span>Série</span><strong>{selected.streakActuel} jours · record {selected.streakMax}</strong></div>
                  <div><span>Transactions de points</span><strong>{selected._count.pointsTransactions}</strong></div>
                  <div><span>Dernière visite</span><strong>{dateLabel(selected.derniereVisiteAt, true)}</strong></div>
                  <div><span>Participations aux tirages</span><strong>{selected._count.raffleTickets ?? "Indisponible en V2"}</strong></div>
                  <div><span>Sessions de visionnage</span><strong>{selected._count.watchSessions ?? "Indisponible en V2"}</strong></div>
                </div>
                <div className="admin-modal-actions"><button className="vd-text-button" onClick={() => void showAudit()}>Consulter le journal d’audit <span aria-hidden="true">↗</span></button><button className="vd-modal-secondary" onClick={() => setConfirmStatus(true)} disabled={savingStatus || (selected.id === profile.id && selected.actif)}>{selected.id === profile.id && selected.actif ? "Compte administrateur actuel" : selected.actif ? "Désactiver le compte" : "Activer le compte"}</button></div>
                {selected.id === profile.id && selected.actif && <p className="admin-self-status-note">La session administrateur actuelle ne peut pas être désactivée depuis cet espace.</p>}
                {confirmStatus && <div className="admin-status-confirm" role="group" aria-label="Confirmer la modification du statut"><p>Confirmer {selected.actif ? "la désactivation" : "l’activation"} du compte <strong>{selected.pseudo}</strong> ?</p><div><button className="admin-confirm-cancel" onClick={() => setConfirmStatus(false)}>Annuler</button><button className="admin-confirm-submit" onClick={() => void updateStatus()} disabled={savingStatus}>{savingStatus ? "Mise à jour…" : "Confirmer"}</button></div></div>}
              </>}
            </>}
          </section>
        </div>, document.body,
      )}
      <AdminRaffleManager open={rafflesOpen} onClose={() => setRafflesOpen(false)} />
    </DashboardShell>
  );
}
