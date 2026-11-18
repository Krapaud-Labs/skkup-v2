"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Sponsor = Readonly<{ id: string; nom: string; logoUrl: string | null; actif: boolean }>;
type RaffleLot = Readonly<{
  id: string;
  nom: string;
  valeurEstimee: string;
  quantite: number;
  fournisseur: string;
  sponsorId: string | null;
  sponsor: Readonly<{ id: string; nom: string; logoUrl: string | null }> | null;
  imageUrl: string | null;
}>;
type Raffle = Readonly<{
  id: string;
  titre: string;
  description: string;
  dateOuverture: string;
  dateTirage: string;
  statut: "OUVERT" | "CLOTURE" | "TIRE";
  engagementGraine: string | null;
  ticketsDistribues: number | null;
  gagnantsCount: number | null;
  lots: RaffleLot[];
  drawAvailability: "not_implemented";
}>;
type RafflePage = Readonly<{
  items: Raffle[];
  total: number;
  page: number;
  limit: number;
  availability: Readonly<{ draws: "not_implemented"; tickets: "not_implemented" }>;
}>;
type AuditEvent = Readonly<{ id: string; action: string; actor: Readonly<{ id: string; pseudo: string }>; createdAt: string }>;
type RaffleHistory = Readonly<{ items: AuditEvent[]; draws: null; availability: Readonly<{ draws: "not_implemented" }> }>;
type LotDraft = {
  nom: string;
  valeurEstimee: string;
  quantite: string;
  fournisseur: string;
  sponsorId: string;
  imageUrl: string;
};
type RaffleDraft = {
  titre: string;
  description: string;
  dateOuverture: string;
  dateTirage: string;
  engagementGraine: string;
  lots: LotDraft[];
};
type View = "list" | "detail" | "edit";

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
  return response.json() as Promise<T>;
}

function localDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date inconnue";
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function toLocalInput(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function emptyLot(): LotDraft {
  return { nom: "", valeurEstimee: "", quantite: "1", fournisseur: "", sponsorId: "", imageUrl: "" };
}

function emptyRaffle(): RaffleDraft {
  return { titre: "", description: "", dateOuverture: "", dateTirage: "", engagementGraine: "", lots: [emptyLot()] };
}

function raffleDraft(raffle: Raffle): RaffleDraft {
  return {
    titre: raffle.titre,
    description: raffle.description,
    dateOuverture: toLocalInput(raffle.dateOuverture),
    dateTirage: toLocalInput(raffle.dateTirage),
    engagementGraine: raffle.engagementGraine ?? "",
    lots: raffle.lots.map((lot) => ({
      nom: lot.nom,
      valeurEstimee: lot.valeurEstimee,
      quantite: String(lot.quantite),
      fournisseur: lot.fournisseur,
      sponsorId: lot.sponsorId ?? "",
      imageUrl: lot.imageUrl ?? "",
    })),
  };
}

function statusLabel(status: Raffle["statut"]) {
  return ({ OUVERT: "Ouvert", CLOTURE: "Clôturé", TIRE: "Tirage effectué" })[status];
}

function auditLabel(action: string) {
  return ({ RAFFLE_CREATED: "Configuration créée", RAFFLE_UPDATED: "Configuration modifiée" })[action] ?? "Événement d’administration";
}

export function AdminRaffleManager({ open, onClose }: Readonly<{ open: boolean; onClose: () => void }>) {
  const [view, setView] = useState<View>("list");
  const [items, setItems] = useState<Raffle[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Raffle | null>(null);
  const [history, setHistory] = useState<AuditEvent[]>([]);
  const [sponsors, setSponsors] = useState<Sponsor[]>([]);
  const [sponsorsError, setSponsorsError] = useState(false);
  const [draft, setDraft] = useState<RaffleDraft>(emptyRaffle);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const dialogRef = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  const loadPage = useCallback(async (targetPage: number) => {
    setLoading(true);
    setError("");
    try {
      const result = await request<RafflePage>(`/admin/raffles?page=${targetPage}&limit=20`);
      setItems(result.items);
      setTotal(result.total);
      setPage(result.page);
    } catch (loadError) {
      setItems([]);
      setError(loadError instanceof Error ? loadError.message : "Impossible de charger les tirages.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (!open) return;
    closeButton.current?.focus();
    void loadPage(1);
    setSponsorsError(false);
    void request<Sponsor[]>("/admin/sponsors?page=1&limit=100")
      .then(setSponsors)
      .catch(() => { setSponsorsError(true); });
  }, [open, loadPage]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
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
  }, [open, onClose]);

  const openDetails = async (raffle: Raffle) => {
    setSelected(raffle);
    setHistory([]);
    setError("");
    setView("detail");
    setLoading(true);
    try {
      const [details, audit] = await Promise.all([
        request<Raffle>(`/admin/raffles/${encodeURIComponent(raffle.id)}`),
        request<RaffleHistory>(`/admin/raffles/${encodeURIComponent(raffle.id)}/history`),
      ]);
      setSelected(details);
      setHistory(audit.items);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Impossible de charger le détail du tirage.");
    } finally { setLoading(false); }
  };

  const beginCreate = () => {
    setSelected(null);
    setDraft(emptyRaffle());
    setNotice("");
    setError("");
    setView("edit");
  };

  const beginEdit = () => {
    if (!selected) return;
    setDraft(raffleDraft(selected));
    setNotice("");
    setError("");
    setView("edit");
  };

  const updateDraft = (key: keyof RaffleDraft, value: string) => setDraft((current) => ({ ...current, [key]: value }));
  const updateLot = (index: number, key: keyof LotDraft, value: string) => setDraft((current) => ({
    ...current,
    lots: current.lots.map((lot, lotIndex) => lotIndex === index ? { ...lot, [key]: value } : lot),
  }));

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    const lots = draft.lots.map((lot) => ({
      nom: lot.nom.trim(),
      valeurEstimee: lot.valeurEstimee.trim(),
      quantite: Number(lot.quantite),
      fournisseur: lot.fournisseur.trim(),
      ...(lot.sponsorId ? { sponsorId: lot.sponsorId } : {}),
      ...(lot.imageUrl.trim() ? { imageUrl: lot.imageUrl.trim() } : {}),
    }));
    const payload = selected ? {
      titre: draft.titre.trim(),
      description: draft.description.trim(),
      dateTirage: new Date(draft.dateTirage).toISOString(),
      lots,
    } : {
      titre: draft.titre.trim(),
      description: draft.description.trim(),
      dateOuverture: new Date(draft.dateOuverture).toISOString(),
      dateTirage: new Date(draft.dateTirage).toISOString(),
      engagementGraine: draft.engagementGraine.trim(),
      lots,
    };
    try {
      const saved = await request<Raffle>(selected
        ? `/admin/raffles/${encodeURIComponent(selected.id)}`
        : "/admin/raffles", { method: selected ? "PATCH" : "POST", body: JSON.stringify(payload) });
      setSelected(saved);
      setNotice(selected ? "La configuration a été mise à jour." : "Le tirage a été créé et son annonce publiée.");
      setView("detail");
      await loadPage(page);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Impossible d’enregistrer cette configuration.");
    } finally { setSaving(false); }
  };

  const backToList = () => { setView("list"); setSelected(null); setError(""); setNotice(""); };
  if (!open || typeof document === "undefined") return null;

  const raffleCount = total.toLocaleString("fr-FR");
  const pageCount = Math.max(1, Math.ceil(total / 20));
  const canEdit = selected?.statut === "OUVERT";
  const sponsorOptions = [...sponsors];
  for (const lot of selected?.lots ?? []) {
    if (lot.sponsor && !sponsorOptions.some((sponsor) => sponsor.id === lot.sponsor?.id)) {
      sponsorOptions.push({ ...lot.sponsor, actif: false });
    }
  }

  return createPortal(
    <div className="vd-backdrop admin-raffle-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="vd-modal admin-modal admin-raffle-modal" ref={dialogRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="admin-raffle-title" data-dashboard-modal>
        <button ref={closeButton} className="vd-modal-close" onClick={onClose} aria-label="Fermer">×</button>
        <p className="vd-eyebrow">CONFIGURATION & PARTENAIRES</p>
        <h2 id="admin-raffle-title">{view === "list" ? "Tirages & lots" : view === "edit" ? selected ? "Modifier le tirage" : "Créer un tirage" : selected?.titre ?? "Détail du tirage"}</h2>
        {view === "list" ? <>
          <p className="admin-raffle-intro">Prépare les tirages et leurs lots dans l’univers Skkup.</p>
          <div className="admin-raffle-actions"><span>{raffleCount} tirage{total > 1 ? "s" : ""}</span><button className="vd-text-button" onClick={beginCreate}>Nouveau tirage <span aria-hidden="true">＋</span></button></div>
          <div className="admin-raffle-limit" role="note"><span aria-hidden="true">✦</span><span>Le lancement d’un tirage et l’attribution des tickets de participation seront ajoutés dans une étape séparée. Les tickets à gratter CLASSIC/PREMIUM sont distincts.</span></div>
          {error && <div className="admin-state admin-state-error" role="alert"><span>{error}</span><button className="vd-text-button" onClick={() => void loadPage(page)}>Réessayer</button></div>}
          {loading ? <p className="vd-empty" role="status">Chargement des tirages…</p> : items.length ? <div className="admin-raffle-list" aria-label="Tirages configurés">
            {items.map((raffle) => <button className="admin-raffle-row" key={raffle.id} onClick={() => void openDetails(raffle)} aria-haspopup="dialog">
              <span className="admin-raffle-gem" aria-hidden="true">✧</span>
              <span className="admin-raffle-identity"><strong>{raffle.titre}</strong><small>{raffle.lots.length} lot{raffle.lots.length > 1 ? "s" : ""} · Tirage le {localDate(raffle.dateTirage)}</small></span>
              <span className={`admin-raffle-status ${raffle.statut.toLowerCase()}`}>{statusLabel(raffle.statut)}</span>
              <i aria-hidden="true">›</i>
            </button>)}
          </div> : <div className="admin-raffle-empty"><span aria-hidden="true">◈</span><strong>Aucun tirage configuré</strong><small>Crée une première configuration pour préparer les prochains lots.</small><button className="vd-modal-secondary" onClick={beginCreate}>Créer un tirage</button></div>}
          <div className="admin-audit-pagination"><button className="admin-confirm-cancel" onClick={() => void loadPage(Math.max(1, page - 1))} disabled={page <= 1 || loading}>Précédent</button><span>Page {page} / {pageCount}</span><button className="admin-confirm-cancel" onClick={() => void loadPage(Math.min(pageCount, page + 1))} disabled={page >= pageCount || loading}>Suivant</button></div>
        </> : view === "detail" && selected ? <>
          <div className="admin-modal-actions admin-raffle-detail-actions"><button className="vd-text-button" onClick={backToList}>← Tous les tirages</button><button className="vd-modal-secondary" onClick={beginEdit} disabled={!canEdit}>{canEdit ? "Modifier la configuration" : "Configuration verrouillée"}</button></div>
          {notice && <p className="admin-notice" role="status">{notice}</p>}
          {error && <div className="admin-state admin-state-error" role="alert"><span>{error}</span><button className="vd-text-button" onClick={() => void openDetails(selected)}>Réessayer</button></div>}
          {loading ? <p className="vd-empty" role="status">Chargement du détail…</p> : <div className="admin-raffle-detail-scroll">
            <div className="admin-raffle-summary"><span className={`admin-raffle-status ${selected.statut.toLowerCase()}`}>{statusLabel(selected.statut)}</span><p>{selected.description}</p><div><span>Ouverture<strong>{localDate(selected.dateOuverture)}</strong></span><span>Tirage prévu<strong>{localDate(selected.dateTirage)}</strong></span><span>Participations au tirage<strong>{selected.ticketsDistribues ?? "Non disponible"}</strong></span></div></div>
            <section className="admin-raffle-lots" aria-labelledby="admin-raffle-lots-title"><header><h3 id="admin-raffle-lots-title">Lots & partenaires</h3><span>{selected.lots.length} référence{selected.lots.length > 1 ? "s" : ""}</span></header>{selected.lots.map((lot) => <article key={lot.id}><span className="admin-raffle-lot-gem" aria-hidden="true">✦</span><span><strong>{lot.nom}</strong><small>{lot.fournisseur}{lot.sponsor ? ` · ${lot.sponsor.nom}` : ""} · ×{lot.quantite}</small></span><b>{Number(lot.valeurEstimee).toLocaleString("fr-FR", { style: "currency", currency: "EUR" })}</b></article>)}</section>
            <div className="admin-raffle-commitment"><span>Engagement SHA-256</span><code>{selected.engagementGraine ?? "Non renseigné"}</code><small>Le secret de tirage n’est jamais affiché dans cette interface.</small></div>
            <section className="admin-raffle-history" aria-labelledby="admin-raffle-history-title"><h3 id="admin-raffle-history-title">Historique de configuration</h3>{history.length ? history.slice(0, 6).map((event) => <article key={event.id}><span className="admin-audit-dot" aria-hidden="true"/><span><strong>{auditLabel(event.action)}</strong><small>{event.actor.pseudo} · {localDate(event.createdAt)}</small></span></article>) : <p>Aucun événement enregistré.</p>}</section>
          </div>}
        </> : <form className="admin-raffle-form" onSubmit={(event) => void save(event)}>
          <div className="admin-modal-actions admin-raffle-detail-actions"><button type="button" className="vd-text-button" onClick={() => selected ? setView("detail") : setView("list")}>← Retour</button><span className="admin-form-required">Champs requis <b>*</b></span></div>
          {error && <p className="admin-dialog-error" role="alert">{error}</p>}
          <div className="admin-raffle-detail-scroll admin-raffle-form-scroll">
            <label className="admin-form-field"><span>Nom du tirage <b>*</b></span><input required maxLength={160} value={draft.titre} onChange={(event) => updateDraft("titre", event.target.value)} /></label>
            <label className="admin-form-field"><span>Description <b>*</b></span><textarea required maxLength={2000} rows={3} value={draft.description} onChange={(event) => updateDraft("description", event.target.value)} /></label>
            {!selected && <label className="admin-form-field"><span>Date d’ouverture <b>*</b></span><input type="datetime-local" required value={draft.dateOuverture} onChange={(event) => updateDraft("dateOuverture", event.target.value)} /></label>}
            <label className="admin-form-field"><span>Date du tirage <b>*</b></span><input type="datetime-local" required value={draft.dateTirage} onChange={(event) => updateDraft("dateTirage", event.target.value)} /></label>
            {!selected && <label className="admin-form-field"><span>Engagement SHA-256 <b>*</b></span><input required minLength={64} maxLength={64} pattern="[a-fA-F0-9]{64}" value={draft.engagementGraine} onChange={(event) => updateDraft("engagementGraine", event.target.value)} autoComplete="off" /><small>64 caractères hexadécimaux. Saisis uniquement l’empreinte publique, jamais le secret.</small></label>}
            <fieldset className="admin-raffle-lot-editor"><legend>Lots du tirage <b>*</b></legend>
              {draft.lots.map((lot, index) => <div className="admin-raffle-lot-card" key={`lot-${index}`}><header><strong>Lot {index + 1}</strong>{draft.lots.length > 1 && <button type="button" onClick={() => setDraft((current) => ({ ...current, lots: current.lots.filter((_, lotIndex) => lotIndex !== index) }))}>Retirer</button>}</header>
                <label className="admin-form-field"><span>Nom du lot <b>*</b></span><input required maxLength={160} value={lot.nom} onChange={(event) => updateLot(index, "nom", event.target.value)} /></label>
                <div className="admin-raffle-input-row"><label className="admin-form-field"><span>Valeur estimée (€) <b>*</b></span><input required type="number" min="0" max="99999999" step="0.01" value={lot.valeurEstimee} onChange={(event) => updateLot(index, "valeurEstimee", event.target.value)} /></label><label className="admin-form-field"><span>Quantité <b>*</b></span><input required type="number" min="1" step="1" value={lot.quantite} onChange={(event) => updateLot(index, "quantite", event.target.value)} /></label></div>
                <label className="admin-form-field"><span>Fournisseur <b>*</b></span><input required maxLength={160} value={lot.fournisseur} onChange={(event) => updateLot(index, "fournisseur", event.target.value)} /></label>
                <label className="admin-form-field"><span>Sponsor associé</span><select value={lot.sponsorId} onChange={(event) => updateLot(index, "sponsorId", event.target.value)}><option value="">Aucun sponsor</option>{sponsorOptions.filter((sponsor) => sponsor.actif || sponsor.id === lot.sponsorId).map((sponsor) => <option key={sponsor.id} value={sponsor.id}>{sponsor.nom}{sponsor.actif ? "" : " (inactif)"}</option>)}</select><small>{sponsorsError ? "Catalogue temporairement indisponible; le sponsor actuel est conservé." : "Le fournisseur reste affiché même si le sponsor change."}</small></label>
                <label className="admin-form-field"><span>Image du lot (URL HTTPS)</span><input type="url" pattern="https://.+" maxLength={2048} value={lot.imageUrl} onChange={(event) => updateLot(index, "imageUrl", event.target.value)} placeholder="https://…" /></label>
              </div>)}
              {draft.lots.length < 100 && <button type="button" className="admin-raffle-add-lot" onClick={() => setDraft((current) => ({ ...current, lots: [...current.lots, emptyLot()] }))}>＋ Ajouter un lot</button>}
            </fieldset>
          </div>
          <div className="admin-raffle-form-footer"><button type="button" className="admin-confirm-cancel" onClick={() => selected ? setView("detail") : setView("list")}>Annuler</button><button type="submit" className="vd-modal-secondary" disabled={saving}>{saving ? "Enregistrement…" : selected ? "Enregistrer les changements" : "Créer le tirage"}</button></div>
        </form>}
      </section>
    </div>, document.body,
  );
}
