import type { MouseEventHandler, ReactNode } from "react";

export type DashboardRole = "VIEWER" | "ADMIN";

type DashboardShellProps = Readonly<{
  role: DashboardRole;
  profileName?: string;
  modalOpen?: boolean;
  onAccountClick: MouseEventHandler<HTMLButtonElement>;
  children: ReactNode;
}>;

/** Shared Dashboard frame. Role-specific sections are supplied by each route. */
export function DashboardShell({ role, profileName, modalOpen = false, onAccountClick, children }: DashboardShellProps) {
  return (
    <main className="viewer-dashboard" data-dashboard-role={role} inert={modalOpen || undefined}>
      <header className="vd-header">
        <a className="vd-brand" href="/dashboard" aria-label="Skkup, tableau de bord"><span className="vd-brand-mark">S</span><span>skkup</span></a>
        <div className="vd-header-actions">
          <span className="vd-online"><i /> Espace {role === "VIEWER" ? "Viewer" : "Admin"}</span>
          <button className="vd-account" onClick={onAccountClick} aria-haspopup="dialog">
            <span className="vd-avatar">{profileName?.slice(0, 1).toUpperCase() ?? "…"}</span>
            <span>{profileName ?? "Mon compte"}</span><span aria-hidden="true">⌄</span>
          </button>
        </div>
      </header>
      <div className="vd-shell-content">{children}</div>
    </main>
  );
}
