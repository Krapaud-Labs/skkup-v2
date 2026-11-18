"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type Raffle = { id: string; titre: string; description: string; dateOuverture: string; dateTirage: string; statut: "OUVERT" | "CLOTURE" | "TIRE"; resultatPublieAt: string | null; ticketsDistribues: number; lots: Array<{ id: string; nom: string; valeurEstimee: string; quantite: number; fournisseur: string; imageUrl: string | null }> };
type MyTicket = { id: string; raffleId: string; raffleTitre: string; createdAt: string; statut: string; gagnant: boolean; lot?: { nom: string } | null };
type MyTicketPage = { tickets: MyTicket[]; page: number; totalPages: number; total: number };
type Result = { id: string; titre: string; statut: string; dateTirage: string; resultatPublieAt: string; graineAleatoire: string; empreinteParticipants: string; nombreParticipants: number; gagnants: Array<{ lotId: string; lotNom: string; ticketId: string; pseudo: string }> };
type View = "catalog" | "history" | "detail" | "result";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { ...init, credentials: "include", headers: { ...(init?.headers ?? {}), ...(init?.body ? { "Content-Type": "application/json" } : {}) } });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

function dateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Date à confirmer" : new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export function ViewerRaffleCenter({ open, onClose, onPointsChanged }: Readonly<{ open: boolean; onClose: () => void; onPointsChanged: () => void }>) {
  const [view, setView] = useState<View>("catalog");
  const [raffles, setRaffles] = useState<Raffle[]>([]);
  const [tickets, setTickets] = useState<MyTicket[]>([]);
  const [selected, setSelected] = useState<Raffle | MyTicket | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const pageSize = 20;

  const loadCatalog = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const data = await request<Raffle[]>("/raffles");
      setRaffles(data);
    } catch { setError("Impossible de charger les concours pour le moment."); }
    finally { setLoading(false); }
  }, []);

  const loadHistory = useCallback(async (nextPage = 1, append = false) => {
    setLoading(true); setError("");
    try {
      const data = await request<MyTicketPage>(`/me/raffle-tickets?page=${nextPage}&limit=${pageSize}`);
      setTickets((current) => append ? [...current, ...data.tickets] : data.tickets);
      setPage(data.page); setTotalPages(data.totalPages);
    } catch { setError("Impossible de charger tes participations."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    setView("catalog"); setSelected(null); setResult(null); setNotice("");
    void loadCatalog();
    void loadHistory(1);
  }, [loadCatalog, loadHistory, open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !saving) {
        if (view === "detail" || view === "result") { setView("catalog"); setSelected(null); setResult(null); }
        else onClose();
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const elements = Array.from(dialogRef.current.querySelectorAll<HTMLElement>("button:not([disabled]),a[href],input:not([disabled]),[tabindex]:not([tabindex='-1'])"));
      if (!elements.length) return;
      if (event.shiftKey && document.activeElement === elements[0]) { event.preventDefault(); elements.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === elements.at(-1)) { event.preventDefault(); elements[0].focus(); }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose, open, saving, view]);

  const openRaffle = (raffle: Raffle) => { setSelected(raffle); setView("detail"); setError(""); setNotice(""); };
  const showResult = async (raffle: Raffle) => {
    setSelected(raffle); setView("result"); setLoading(true); setError(""); setResult(null);
    try { setResult(await request<Result>(`/raffles/${encodeURIComponent(raffle.id)}/result`)); }
    catch (resultError) { setError(resultError instanceof Error && resultError.message === "HTTP 404" ? "Les résultats seront disponibles après le tirage." : "Impossible de charger les résultats."); }
    finally { setLoading(false); }
  };
  const register = async (raffle: Raffle) => {
    setSaving(true); setError(""); setNotice("");
    try {
      await request(`/me/raffles/${encodeURIComponent(raffle.id)}/register`, { method: "POST" });
      setNotice("Participation confirmée. 2 500 points ont été utilisés.");
      await loadHistory(1);
      onPointsChanged();
    } catch (registerError) {
      const message = registerError instanceof Error ? registerError.message : "";
      setError(message === "HTTP 409" ? "Inscription impossible : concours fermé, déjà inscrit ou solde insuffisant." : "Impossible d’enregistrer ta participation.");
    } finally { setSaving(false); }
  };

  if (!open || typeof document === "undefined") return null;
  const selectedRaffle = selected && "dateOuverture" in selected ? selected : null;
  const selectedTicket = selected && "raffleTitre" in selected ? selected : null;
  const myRaffleIds = new Set(tickets.map((ticket) => ticket.raffleId));
  const drawStatusLabel = (status: Raffle["statut"]) => ({ OUVERT: "Ouvert", CLOTURE: "Clôturé", TIRE: "Résultats publiés" })[status];

  return createPortal(<div className="vd-backdrop vd-raffle-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !saving) onClose(); }}>
    <section ref={dialogRef} tabIndex={-1} className="vd-modal vd-raffle-dialog" role="dialog" aria-modal="true" aria-labelledby="vd-raffle-title" data-dashboard-modal>
      <button ref={closeRef} type="button" className="vd-modal-close" onClick={onClose} disabled={saving} aria-label="Fermer">×</button>
      <p className="vd-eyebrow">CONCOURS SKKUP</p>
      <h2 id="vd-raffle-title">{view === "result" ? "Résultats du tirage" : view === "detail" ? selectedRaffle?.titre ?? "Ma participation" : "Participe aux tirages"}</h2>
      {(view === "catalog" || view === "history") && <div className="vd-raffle-tabs" role="tablist" aria-label="Concours"><button type="button" role="tab" aria-selected={view === "catalog"} className={view === "catalog" ? "active" : ""} onClick={() => { setView("catalog"); setError(""); }}>Concours ouverts</button><button type="button" role="tab" aria-selected={view === "history"} className={view === "history" ? "active" : ""} onClick={() => { setView("history"); setError(""); }}>Mes participations</button></div>}
      {view === "catalog" && <><p className="vd-raffle-intro">Une participation coûte <strong>2 500 points</strong>. Elle est séparée de tes tickets à gratter CLASSIC et PREMIUM.</p><div className="vd-raffle-list" aria-busy={loading}>
        {loading ? <p className="vd-empty" role="status">Chargement des concours…</p> : raffles.length ? raffles.map((raffle) => <article className="vd-raffle-row" key={raffle.id}><span className="vd-raffle-gem" aria-hidden="true">✧</span><span className="vd-raffle-copy"><strong>{raffle.titre}</strong><small>{raffle.lots.length} lot{raffle.lots.length === 1 ? "" : "s"} · Tirage {dateLabel(raffle.dateTirage)}</small></span><span className={`vd-raffle-status ${raffle.statut.toLowerCase()}`}>{drawStatusLabel(raffle.statut)}</span><div className="vd-raffle-actions"><button type="button" className="vd-scratch-open" onClick={() => openRaffle(raffle)}>Détails</button>{raffle.statut === "TIRE" && <button type="button" className="vd-scratch-open" onClick={() => void showResult(raffle)}>Résultats</button>}</div></article>) : !error && <p className="vd-empty">Aucun concours n’est disponible pour le moment.</p>}
        {error && <p className="vd-scratch-error" role="alert">{error}</p>}</div></>}
      {view === "history" && <><p className="vd-raffle-intro">Tes participations, achats et résultats sont regroupés ici.</p><div className="vd-raffle-list" aria-busy={loading}>{loading ? <p className="vd-empty" role="status">Chargement de tes participations…</p> : tickets.length ? tickets.map((ticket) => <article className="vd-raffle-row" key={ticket.id}><span className="vd-raffle-gem" aria-hidden="true">✦</span><span className="vd-raffle-copy"><strong>{ticket.raffleTitre}</strong><small>Participation du {dateLabel(ticket.createdAt)} · {ticket.statut}</small></span><span className={`vd-raffle-status ${ticket.gagnant ? "tire" : ""}`}>{ticket.gagnant ? `Gagnant${ticket.lot?.nom ? ` · ${ticket.lot.nom}` : ""}` : "Inscrit"}</span><button type="button" className="vd-scratch-open" onClick={() => { setSelected(ticket); setView("detail"); }}>Détails</button></article>) : !error && <p className="vd-empty">Aucune participation pour le moment.</p>}{error && <p className="vd-scratch-error" role="alert">{error}</p>}</div>{page < totalPages && <button type="button" className="vd-scratch-more" disabled={loading} onClick={() => void loadHistory(page + 1, true)}>Afficher plus</button>}</>}
      {view === "detail" && <><div className="vd-raffle-detail">{selectedRaffle ? <><span className={`vd-raffle-status ${selectedRaffle.statut.toLowerCase()}`}>{drawStatusLabel(selectedRaffle.statut)}</span><p>{selectedRaffle.description}</p><dl><div><dt>Ouverture</dt><dd>{dateLabel(selectedRaffle.dateOuverture)}</dd></div><div><dt>Tirage prévu</dt><dd>{dateLabel(selectedRaffle.dateTirage)}</dd></div><div><dt>Lots annoncés</dt><dd>{selectedRaffle.lots.reduce((sum, lot) => sum + lot.quantite, 0)}</dd></div></dl><div className="vd-raffle-lot-list">{selectedRaffle.lots.map((lot) => <div key={lot.id}><strong>{lot.nom}</strong><small>{lot.fournisseur} · ×{lot.quantite}</small></div>)}</div></> : selectedTicket && <><span className="vd-raffle-status">Participation enregistrée</span><p>{selectedTicket.raffleTitre}</p><dl><div><dt>Créée le</dt><dd>{dateLabel(selectedTicket.createdAt)}</dd></div><div><dt>État</dt><dd>{selectedTicket.statut}</dd></div><div><dt>Résultat</dt><dd>{selectedTicket.gagnant ? selectedTicket.lot?.nom ?? "Gagnant" : "Pas de lot attribué"}</dd></div></dl></>}</div>{selectedRaffle && <>{myRaffleIds.has(selectedRaffle.id) ? <p className="vd-scratch-status" role="status">Tu as déjà une participation à ce concours.</p> : <button type="button" className="vd-modal-secondary" disabled={saving || selectedRaffle.statut !== "OUVERT"} onClick={() => void register(selectedRaffle)}>{saving ? "Inscription…" : selectedRaffle.statut !== "OUVERT" ? "Inscriptions fermées" : "Participer · 2 500 points"}</button>}{selectedRaffle.statut === "TIRE" && <button type="button" className="vd-scratch-more" onClick={() => void showResult(selectedRaffle)}>Voir les résultats</button>}</>}{notice && <p className="vd-raffle-notice" role="status">{notice}</p>}{error && <p className="vd-scratch-error" role="alert">{error}</p>}<button type="button" className="vd-text-button" onClick={() => { setView("catalog"); setSelected(null); setError(""); }}>← Retour aux concours</button></>}
      {view === "result" && <>{loading ? <p className="vd-empty" role="status">Chargement des résultats…</p> : result ? <><div className="vd-raffle-proof"><span>{result.nombreParticipants.toLocaleString("fr-FR")} participations</span><small>Résultat publié le {dateLabel(result.resultatPublieAt)}</small></div><div className="vd-raffle-winners" aria-label="Gagnants">{result.gagnants.length ? result.gagnants.map((winner, index) => <article key={`${winner.ticketId}-${winner.lotId}`}><span className="vd-raffle-rank">{index + 1}</span><span><strong>{winner.pseudo}</strong><small>{winner.lotNom}</small></span></article>) : <p className="vd-empty">Aucun gagnant publié.</p>}</div><details className="vd-raffle-audit"><summary>Preuves du tirage</summary><p>Empreinte des participations <code>{result.empreinteParticipants}</code></p><p>Graine publiée <code>{result.graineAleatoire}</code></p></details></> : <p className="vd-scratch-status" role="status">{error || "Résultat indisponible."}</p>}<button type="button" className="vd-text-button" onClick={() => { setView("catalog"); setSelected(null); setResult(null); }}>← Retour aux concours</button></>}
    </section>
  </div>, document.body);
}
