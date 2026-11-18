"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState, type MouseEvent, type PointerEvent } from "react";
import { createPortal } from "react-dom";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const pageSize = 100;

type Page<T> = { items?: T[]; cards?: T[]; tickets?: T[]; totalPages?: number };
type StreakCard = { id: string; streakMilestone: number; createdAt: string; prepared: boolean };
type RewardTicket = { id: string; categorie: "CLASSIC" | "PREMIUM"; origine: string; createdAt: string; prepared: boolean };
type ScratchHistoryItem = { id: string; sourceType: "LEGACY_CARD" | "REWARD_TICKET"; category: "LEGACY" | "CLASSIC" | "PREMIUM"; streakMilestone: number | null; outcome: string; pointsAwarded: number; scratchTicketsAwarded: number; createdAt: string; scratchedAt: string };
type ScratchHistoryPage = { items: ScratchHistoryItem[]; page: number; totalPages: number; total: number };
type ScratchItem = {
  id: string;
  kind: "streak" | "ticket";
  category: "CLASSIC" | "PREMIUM" | null;
  streakMilestone: number | null;
  createdAt: string;
  prepared: boolean;
};
type ScratchOutcome = {
  type: "POINTS" | "NO_WIN" | "SCRATCH_TICKET";
  pointsAwarded: number;
  scratchTicketsAwarded: number;
};
type ScratchResponse = {
  id: string;
  category: string;
  grattee: true;
  outcome: ScratchOutcome;
  soldePoints: number;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    credentials: "include",
    headers: { ...(init?.headers ?? {}) },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

function dateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
}

function itemLabel(item: ScratchItem) {
  if (item.kind === "ticket") return `Ticket à gratter ${item.category}`;
  return `Carte bonus de série · ${item.streakMilestone} jours`;
}

function resultLabel(outcome: ScratchOutcome) {
  if (outcome.type === "POINTS") return `+${outcome.pointsAwarded} points`;
  if (outcome.type === "SCRATCH_TICKET") {
    const count = Math.max(1, outcome.scratchTicketsAwarded);
    return `${count} ticket${count > 1 ? "s" : ""} à gratter CLASSIC`;
  }
  return "Aucun gain cette fois";
}

type ScratchTicketCenterProps = Readonly<{
  open: boolean;
  onClose: () => void;
  onPointsChanged: () => void;
}>;

export function ScratchTicketCenter({ open, onClose, onPointsChanged }: ScratchTicketCenterProps) {
  const [items, setItems] = useState<ScratchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [tab, setTab] = useState<"inventory" | "history">("inventory");
  const [scratchHistory, setScratchHistory] = useState<ScratchHistoryItem[]>([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotalPages, setHistoryTotalPages] = useState(1);
  const [selected, setSelected] = useState<ScratchItem | null>(null);
  const [phase, setPhase] = useState<"prepare" | "scratch" | "saving" | "result">("prepare");
  const [result, setResult] = useState("");
  const [progress, setProgress] = useState(0);
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const scratchTriggerRef = useRef<HTMLButtonElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerDownRef = useRef(false);
  const finalizeStartedRef = useRef(false);
  const revealRef = useRef<(ticket: ScratchItem) => Promise<void>>(async () => undefined);

  const loadPage = useCallback(async (nextPage: number, append: boolean) => {
    setError("");
    if (append) setLoadingMore(true);
    else setLoading(true);
    try {
      const [cardsPage, ticketsPage] = await Promise.all([
        requestJson<Page<StreakCard>>(`/me/scratch-cards?page=${nextPage}&limit=${pageSize}`),
        requestJson<Page<RewardTicket>>(`/me/reward-tickets?page=${nextPage}&limit=${pageSize}`),
      ]);
      const cards = cardsPage.cards ?? cardsPage.items ?? [];
      const tickets = ticketsPage.tickets ?? ticketsPage.items ?? [];
      const nextItems: ScratchItem[] = [
        ...cards.map((card) => ({
          id: card.id,
          kind: "streak" as const,
          category: null,
          streakMilestone: card.streakMilestone,
          createdAt: card.createdAt,
          prepared: card.prepared,
        })),
        ...tickets.map((ticket) => ({
          id: ticket.id,
          kind: "ticket" as const,
          category: ticket.categorie,
          streakMilestone: null,
          createdAt: ticket.createdAt,
          prepared: ticket.prepared,
        })),
      ].sort((left, right) => right.createdAt.localeCompare(left.createdAt));
      setItems((current) => append ? [...current, ...nextItems] : nextItems);
      setPage(nextPage);
      setTotalPages(Math.max(cardsPage.totalPages ?? 1, ticketsPage.totalPages ?? 1));
    } catch {
      setError("Impossible de charger tes tickets à gratter. Réessaie dans un instant.");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  const loadScratchHistory = useCallback(async (nextPage: number, append: boolean) => {
    setError(""); setLoading(true);
    try {
      const data = await requestJson<ScratchHistoryPage>(`/me/scratch-history?page=${nextPage}&limit=20`);
      setScratchHistory((current) => append ? [...current, ...data.items] : data.items);
      setHistoryPage(data.page); setHistoryTotalPages(data.totalPages);
    } catch { setError("Impossible de charger l’historique des tickets."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (!open) return;
    void loadPage(1, false);
    setTab("inventory");
    setSelected(null);
    setPhase("prepare");
    setResult("");
  }, [loadPage, open]);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && phase !== "saving") {
        if (selected) {
          setSelected(null);
          setPhase("prepare");
          setResult("");
          requestAnimationFrame(() => scratchTriggerRef.current?.focus());
        } else {
          onClose();
        }
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]), [href], [tabindex]:not([tabindex='-1'])",
      ));
      if (!focusable.length) return;
      if (event.shiftKey && document.activeElement === focusable[0]) {
        event.preventDefault();
        focusable.at(-1)?.focus();
      } else if (!event.shiftKey && document.activeElement === focusable.at(-1)) {
        event.preventDefault();
        focusable[0]?.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose, open, phase, selected]);

  const prepare = useCallback(async (item: ScratchItem) => {
    setError("");
    setPhase("prepare");
    setProgress(0);
    setSelected(item);
    finalizeStartedRef.current = false;
    if (item.prepared) {
      setPhase("scratch");
      return;
    }
    try {
      const base = item.kind === "streak" ? "/me/scratch-cards" : "/me/reward-tickets";
      await requestJson(`${base}/${encodeURIComponent(item.id)}/prepare`, { method: "POST" });
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, prepared: true } : entry));
      setSelected({ ...item, prepared: true });
      setPhase("scratch");
    } catch (prepareError) {
      setError(prepareError instanceof Error && prepareError.message === "HTTP 409"
        ? "Ce ticket a déjà été gratté. Actualise la liste pour voir les tickets disponibles."
        : "Impossible de préparer ce ticket pour le moment.");
      setSelected(null);
      setPhase("prepare");
    }
  }, []);

  const finalize = useCallback(async (item: ScratchItem) => {
    if (finalizeStartedRef.current) return;
    finalizeStartedRef.current = true;
    setPhase("saving");
    setError("");
    try {
      const base = item.kind === "streak" ? "/me/scratch-cards" : "/me/reward-tickets";
      const response = await requestJson<ScratchResponse>(`${base}/${encodeURIComponent(item.id)}/scratch`, { method: "POST" });
      setResult(resultLabel(response.outcome));
      setPhase("result");
      setItems((current) => current.filter((entry) => entry.id !== item.id));
      onPointsChanged();
    } catch (scratchError) {
      finalizeStartedRef.current = false;
      setPhase("scratch");
      setError(scratchError instanceof Error && scratchError.message === "HTTP 409"
        ? "Ce ticket a déjà été gratté. Actualise la liste pour voir les tickets disponibles."
        : "Le gain n’a pas pu être enregistré. Réessaie sans fermer cette fenêtre.");
    }
  }, [onPointsChanged]);

  useEffect(() => { revealRef.current = finalize; }, [finalize]);

  const paintFoil = useCallback(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { willReadFrequently: true });
    const rect = canvas?.getBoundingClientRect();
    if (!canvas || !context || !rect || rect.width === 0 || rect.height === 0) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    const foil = context.createLinearGradient(0, 0, rect.width, rect.height);
    foil.addColorStop(0, "#f8fafc");
    foil.addColorStop(0.22, "#bfc9d7");
    foil.addColorStop(0.48, "#eef2f7");
    foil.addColorStop(0.72, "#aeb8c8");
    foil.addColorStop(1, "#f8fafc");
    context.globalCompositeOperation = "source-over";
    context.fillStyle = foil;
    context.fillRect(0, 0, rect.width, rect.height);
    context.strokeStyle = "rgb(255 255 255 / 48%)";
    context.lineWidth = 1;
    for (let y = 5; y < rect.height; y += 8) {
      context.beginPath();
      context.moveTo(0, y);
      context.lineTo(rect.width, y - 3);
      context.stroke();
    }
    context.fillStyle = "#34445a";
    context.font = `700 ${Math.max(12, Math.min(18, rect.width * 0.035))}px Arial`;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText("GRATTEZ ICI", rect.width / 2, rect.height / 2);
  }, []);

  useEffect(() => {
    if (open && selected && phase === "scratch") {
      const frame = window.requestAnimationFrame(paintFoil);
      const observer = new ResizeObserver(paintFoil);
      if (canvasRef.current) observer.observe(canvasRef.current);
      return () => { window.cancelAnimationFrame(frame); observer.disconnect(); };
    }
  }, [open, paintFoil, phase, selected]);

  const updateProgress = () => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { willReadFrequently: true });
    if (!canvas || !context) return;
    const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
    const stride = 4 * 20;
    let transparent = 0;
    let sampled = 0;
    for (let index = 3; index < data.length; index += stride) {
      sampled += 1;
      if (data[index] < 32) transparent += 1;
    }
    const ratio = sampled ? transparent / sampled : 0;
    setProgress(ratio);
    const ticket = selected;
    if (ratio >= 0.9 && ticket && phase === "scratch") void revealRef.current(ticket);
  };

  const erasePoint = (x: number, y: number) => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { willReadFrequently: true });
    const rect = canvas?.getBoundingClientRect();
    if (!canvas || !context || !rect) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    context.save();
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.globalCompositeOperation = "destination-out";
    context.beginPath();
    context.arc(x - rect.left, y - rect.top, 24, 0, Math.PI * 2);
    context.fill();
    context.restore();
  };

  const onPointerDown = (event: PointerEvent<HTMLCanvasElement>) => {
    if (phase !== "scratch" || !selected) return;
    pointerDownRef.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
    erasePoint(event.clientX, event.clientY);
    updateProgress();
  };
  const onPointerMove = (event: PointerEvent<HTMLCanvasElement>) => {
    if (!pointerDownRef.current || phase !== "scratch") return;
    erasePoint(event.clientX, event.clientY);
    updateProgress();
  };
  const onPointerUp = (event: PointerEvent<HTMLCanvasElement>) => {
    pointerDownRef.current = false;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    updateProgress();
  };

  const startScratch = (item: ScratchItem, event: MouseEvent<HTMLButtonElement>) => {
    scratchTriggerRef.current = event.currentTarget;
    void prepare(item);
  };
  const returnToInventory = () => {
    setSelected(null);
    setPhase("prepare");
    setResult("");
    setError("");
    requestAnimationFrame(() => closeRef.current?.focus());
  };

  if (!open || typeof document === "undefined") return null;
  const availableClassic = items.filter((item) => item.category === "CLASSIC").length;
  const availablePremium = items.filter((item) => item.category === "PREMIUM").length;
  const selectedImage = selected?.category === "PREMIUM"
    ? "/images/tickets/scratch-premium.png"
    : selected?.category === "CLASSIC"
      ? "/images/tickets/scratch-classic.png"
      : null;

  return createPortal(
    <div className="vd-backdrop vd-scratch-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && phase !== "saving") onClose(); }}>
      <section ref={dialogRef} tabIndex={-1} className="vd-modal vd-scratch-dialog" role="dialog" aria-modal="true" aria-labelledby="vd-scratch-title" aria-describedby={selected ? "vd-scratch-hint" : undefined} data-dashboard-modal>
        <button ref={closeRef} type="button" className="vd-modal-close" onClick={onClose} disabled={phase === "saving"} aria-label="Fermer">×</button>
        {selected ? <>
          <p className="vd-eyebrow">{selected.kind === "ticket" ? "TON TICKET À GRATTER" : "TON BONUS DE SÉRIE"}</p>
          <h2 id="vd-scratch-title">{phase === "result" ? "Ton résultat" : itemLabel(selected)}</h2>
          {selectedImage && phase !== "result" && <p className="vd-scratch-image-note">Ticket à gratter {selected.category}</p>}
          {phase === "prepare" && <div className="vd-scratch-status" role="status" aria-live="polite">Préparation du ticket…</div>}
          {phase === "scratch" && <>
            <div className="vd-scratch-surface">
              {selectedImage && <Image className="vd-scratch-art" src={selectedImage} alt="" aria-hidden="true" width={1774} height={887} priority />}
              <div className="vd-scratch-result" aria-live="polite">Gratte la surface pour découvrir ton gain.</div>
              <canvas ref={canvasRef} aria-hidden="true" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp} />
            </div>
            <p id="vd-scratch-hint" className="vd-scratch-hint">Gratte avec ta souris ou ton doigt, ou utilise le bouton pour révéler ton gain.</p>
            <div className="vd-scratch-progress" role="progressbar" aria-label="Progression du grattage" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)}><span style={{ width: `${Math.round(progress * 100)}%` }} /></div>
            <button type="button" className="vd-modal-secondary vd-scratch-action" onClick={() => selected && void finalize(selected)} disabled={phase !== "scratch"}>Révéler mon gain</button>
          </>}
          {phase === "saving" && <p className="vd-scratch-status" role="status" aria-live="polite">Enregistrement du résultat…</p>}
          {phase === "result" && <>
            <div className="vd-scratch-reward" role="status"><span aria-hidden="true">✦</span><strong>{result}</strong></div>
            <button type="button" className="vd-modal-secondary vd-scratch-action" onClick={returnToInventory}>Retour à mes tickets</button>
          </>}
          {error && <p className="vd-scratch-error" role="alert">{error}</p>}
        </> : <>
          <p className="vd-eyebrow">TES RÉCOMPENSES</p>
          <h2 id="vd-scratch-title">{tab === "inventory" ? "Mes tickets à gratter" : "Historique des grattages"}</h2>
          <div className="vd-scratch-tabs" role="tablist" aria-label="Tickets à gratter"><button type="button" role="tab" aria-selected={tab === "inventory"} className={tab === "inventory" ? "active" : ""} onClick={() => { setTab("inventory"); setError(""); }}>À gratter</button><button type="button" role="tab" aria-selected={tab === "history"} className={tab === "history" ? "active" : ""} onClick={() => { setTab("history"); void loadScratchHistory(1, false); }}>Historique</button></div>
          {tab === "inventory" && <><p className="vd-scratch-intro">Les tickets CLASSIC et PREMIUM sont à gratter. Ils sont distincts des participations au concours.</p>
          {availablePremium > 0 && <p className="vd-premium-notice" role="note">Le grattage PREMIUM est temporairement indisponible pendant la validation de son résultat spécial. Tes tickets restent disponibles et aucun gain ni participation n’est attribué pendant cette attente.</p>}
          <div className="vd-scratch-counts" aria-label="Tickets à gratter disponibles">
            <span><strong>{availableClassic}</strong> CLASSIC</span><span><strong>{availablePremium}</strong> PREMIUM</span><span><strong>{items.filter((item) => item.kind === "streak").length}</strong> bonus de série</span>
          </div>
          <div className="vd-scratch-list" aria-live="polite" aria-busy={loading}>
            {loading ? <p className="vd-empty" role="status">Chargement de tes tickets…</p> : items.length ? items.map((item) => <article className="vd-scratch-row" key={`${item.kind}-${item.id}`}>
              <div className={`vd-scratch-row-mark ${item.category === "PREMIUM" ? "premium" : item.kind === "streak" ? "streak" : "classic"}`} aria-hidden="true">{item.category === "PREMIUM" ? "✦" : item.kind === "streak" ? "♨" : "✧"}</div>
              <div className="vd-scratch-row-copy"><strong>{itemLabel(item)}</strong><small>{dateLabel(item.createdAt)}{item.prepared ? " · Prêt à gratter" : ""}</small></div>
              {item.category === "PREMIUM" ? <div className="vd-premium-locked" aria-label="Grattage Premium temporairement indisponible"><span>En attente</span><small>Grattage temporairement indisponible</small></div> : <button ref={item.id === scratchTriggerRef.current?.dataset.scratchId ? scratchTriggerRef : null} type="button" className="vd-scratch-open" data-scratch-id={`${item.kind}:${item.id}`} onClick={(event) => startScratch(item, event)}>{item.prepared ? "Reprendre" : "Gratter"}<span aria-hidden="true">›</span></button>}
            </article>) : !error && <p className="vd-empty">Tu n’as pas encore de ticket à gratter. Tes prochaines récompenses apparaîtront ici.</p>}
            {error && !loading && <p className="vd-scratch-error" role="alert">{error}</p>}
          </div>
          {!loading && page < totalPages && <button type="button" className="vd-scratch-more" onClick={() => void loadPage(page + 1, true)} disabled={loadingMore}>{loadingMore ? "Chargement…" : "Afficher plus"}</button>}
          </>}
          {tab === "history" && <><p className="vd-scratch-intro">Résultats des tickets déjà grattés.</p><div className="vd-scratch-list" aria-live="polite" aria-busy={loading}>{loading ? <p className="vd-empty" role="status">Chargement de ton historique…</p> : scratchHistory.length ? scratchHistory.map((entry) => <article className="vd-scratch-row vd-scratch-history-row" key={`${entry.sourceType}-${entry.id}`}><div className={`vd-scratch-row-mark ${entry.category === "PREMIUM" ? "premium" : entry.sourceType === "LEGACY_CARD" ? "streak" : "classic"}`} aria-hidden="true">{entry.category === "PREMIUM" ? "✦" : entry.sourceType === "LEGACY_CARD" ? "♨" : "✧"}</div><div className="vd-scratch-row-copy"><strong>{entry.category === "LEGACY" ? `Bonus de série · ${entry.streakMilestone} jours` : `Ticket à gratter ${entry.category}`}</strong><small>Gratté le {dateLabel(entry.scratchedAt)}</small></div><b className="vd-scratch-history-result">{entry.outcome === "POINTS" ? `+${entry.pointsAwarded} pts` : entry.outcome === "SCRATCH_TICKET" ? `${entry.scratchTicketsAwarded} ticket${entry.scratchTicketsAwarded === 1 ? "" : "s"} CLASSIC` : entry.outcome === "NO_WIN" ? "Aucun gain" : "Résultat non disponible"}</b></article>) : !error && <p className="vd-empty">Aucun ticket gratté pour le moment.</p>}{error && <p className="vd-scratch-error" role="alert">{error}</p>}</div>{historyPage < historyTotalPages && <button type="button" className="vd-scratch-more" disabled={loading} onClick={() => void loadScratchHistory(historyPage + 1, true)}>Afficher plus</button>}</>}
        </>}
      </section>
    </div>,
    document.body,
  );
}
