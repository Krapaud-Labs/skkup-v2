"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import type { FormEvent, ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { reglementMarkdown } from "@/content/reglement";
import { reglementMarkdownEn } from "@/content/reglement-en";

type AuthMode = "connexion" | "inscription";
type Locale = "fr" | "en";

const copy = {
  fr: {
    headerAction: { connexion: "S'inscrire", inscription: "Se connecter" },
    intro: {
      connexion: {
        kicker: "Ton espace Skkup",
        title: "Reviens là où",
        accent: "chaque vue compte.",
        description:
          "Connecte-toi pour retrouver tes points, suivre tes tirages et continuer à profiter de tes streams préférés.",
        benefitOne: "Points et historique centralisés",
        benefitTwo: "Tirages publics et vérifiables",
      },
      inscription: {
        kicker: "Bienvenue dans Skkup",
        title: "Ton temps de",
        accent: "visionnage a de la valeur.",
        description:
          "Crée ton compte gratuitement, regarde les streams disponibles et garde une trace claire de tes points et de tes chances.",
        benefitOne: "Gratuit et sans achat obligatoire",
        benefitTwo: "Lots et résultats transparents",
      },
    },
    form: {
      connexion: {
        title: "Connexion",
        subtitle: "Retrouve tes points, ta série et tes cartes à gratter.",
        submit: "Je me connecte",
        submitting: "Connexion en cours...",
        invite: "Pas encore de compte ?",
        switch: "Créer un compte",
      },
      inscription: {
        title: "Créer un compte",
        subtitle: "Gagne des points en regardant tes streams préférés.",
        submit: "Je crée mon compte",
        submitting: "Création en cours...",
        invite: "Tu as déjà un compte ?",
        switch: "Se connecter",
      },
      pseudo: "Pseudo",
      email: "Adresse email",
      password: "Mot de passe",
      confirmPassword: "Confirmer le mot de passe",
      passwordRules: [
        "12 caractères minimum",
        "Une majuscule",
        "Une minuscule",
        "Un chiffre",
        "Un symbole",
      ],
      passwordValid: "Mot de passe conforme",
      passwordInvalid:
        "Le mot de passe ne respecte pas encore toutes les contraintes.",
      mismatch: "Les mots de passe ne correspondent pas.",
      acceptRules: "J’ai lu et j’accepte le règlement du jeu.",
      rulesTitle: "Règlement du jeu",
      rulesDescription:
        "Lis et accepte le règlement du jeu avant de créer ton compte.",
      acceptAction: "J’accepte le règlement et je continue",
      refuseAction: "Refuser et retourner à la vitrine",
      closeRules: "Fermer le règlement",
      genericError: "Une erreur est survenue. Merci de réessayer.",
      networkError: "Impossible de joindre le serveur. Vérifie ta connexion.",
      ruleAcceptanceRequired: "Tu dois accepter le règlement du jeu.",
      passwordRequirements: "Règles du mot de passe",
      loading: "Envoi en cours",
    },
    dashboard: "Tableau de bord",
    ruleExtension:
      "En version 1.0, seuls les visionnages actifs reconnus sur Twitch, YouTube Gaming ou Kick via l'extension officielle Skkup dans Chrome de bureau peuvent générer des points de visionnage. Les applications natives, sur mobile ou ordinateur, les téléphones, tablettes, téléviseurs connectés et navigateurs sans l'extension ne sont pas éligibles. Les autres plateformes de streaming sont hors périmètre. Firefox et Opera ne sont pas pris en charge pour les points de visionnage en version 1.0; leur prise en charge est prévue en version 1.1.",
  },
  en: {
    headerAction: { connexion: "Sign up", inscription: "Log in" },
    intro: {
      connexion: {
        kicker: "Your Skkup space",
        title: "Come back to where",
        accent: "every view counts.",
        description:
          "Log in to find your points, follow your draws and keep enjoying your favourite streams.",
        benefitOne: "Centralized points and history",
        benefitTwo: "Public, verifiable draws",
      },
      inscription: {
        kicker: "Welcome to Skkup",
        title: "Your viewing",
        accent: "time has value.",
        description:
          "Create your free account, watch available streams and keep a clear record of your points and chances.",
        benefitOne: "Free, no purchase required",
        benefitTwo: "Transparent prizes and results",
      },
    },
    form: {
      connexion: {
        title: "Log in",
        subtitle: "Find your points, streak and scratch cards.",
        submit: "Log in",
        submitting: "Logging in...",
        invite: "Do not have an account yet?",
        switch: "Create an account",
      },
      inscription: {
        title: "Create an account",
        subtitle: "Earn points while watching your favourite streams.",
        submit: "Create my account",
        submitting: "Creating account...",
        invite: "Already have an account?",
        switch: "Log in",
      },
      pseudo: "Username",
      email: "Email address",
      password: "Password",
      confirmPassword: "Confirm password",
      passwordRules: [
        "At least 12 characters",
        "One uppercase letter",
        "One lowercase letter",
        "One number",
        "One symbol",
      ],
      passwordValid: "Password meets the requirements",
      passwordInvalid: "The password does not meet all requirements yet.",
      mismatch: "Passwords do not match.",
      acceptRules: "I have read and accept the game rules.",
      rulesTitle: "Game rules",
      rulesDescription:
        "Please read and accept the game rules before creating your account.",
      acceptAction: "I accept the rules and continue",
      refuseAction: "Decline and return to the homepage",
      closeRules: "Close game rules",
      genericError: "Something went wrong. Please try again.",
      networkError: "Could not reach the server. Check your connection.",
      ruleAcceptanceRequired: "You must accept the game rules.",
      passwordRequirements: "Password requirements",
      loading: "Submitting",
    },
    ruleExtension:
      "In version 1.0, only active viewing recognised on Twitch, YouTube Gaming or Kick through the official Skkup extension in desktop Google Chrome can earn viewing points. Native apps on mobile or desktop, phones, tablets, connected TVs, and browsers without the extension are not eligible. Other streaming platforms are out of scope. Firefox and Opera are not supported for viewing points in version 1.0; support is planned for version 1.1.",
    dashboard: "Dashboard",
  },
} as const;

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function RuleText({ text, locale }: { text: string; locale: Locale }) {
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (!listItems.length) return;
    blocks.push(
      <ul className="auth-rules-list" key={`list-${blocks.length}`}>
        {listItems.map((item, index) => (
          <li key={`${item}-${index}`}>{inlineText(item)}</li>
        ))}
      </ul>,
    );
    listItems = [];
  };

  for (const [index, rawLine] of text.split("\n").entries()) {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      continue;
    }
    if (line.startsWith("- ")) {
      listItems.push(line.slice(2));
      continue;
    }
    flushList();
    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      if (heading[1].length === 1) continue;
      if (heading[1].length === 2) {
        blocks.push(<h2 className="auth-rules-heading" key={`heading-${index}`}>{inlineText(heading[2])}</h2>);
        if (/^Article 3\b/.test(heading[2])) {
          blocks.push(<p key={`extension-clause-${index}`}>{copy[locale].ruleExtension}</p>);
        }
      } else {
        blocks.push(<h3 className="auth-rules-subheading" key={`subheading-${index}`}>{inlineText(heading[2])}</h3>);
      }
      continue;
    }
    blocks.push(<p key={`paragraph-${index}`}>{inlineText(line)}</p>);
  }
  flushList();

  return <div className="auth-rules-content">{blocks}</div>;
}

function inlineText(value: string): ReactNode[] {
  const tokens = value.split(/(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*)/g);
  return tokens.map((token, index) => {
    const link = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const [, label, href] = link;
      if (href.startsWith("/")) {
        return (
          <Link href={href} key={`${index}-${label}`}>
            {label}
          </Link>
        );
      }
      return (
        <a href={href} key={`${index}-${label}`} target="_blank" rel="noreferrer">
          {label}
        </a>
      );
    }
    const strong = token.match(/^\*\*([^*]+)\*\*$/);
    if (strong) return strong[1];
    return token.replace(/\*([^*]+)\*/g, "$1").replace(/`([^`]+)`/g, "$1");
  });
}

export function AuthExperience({ mode }: { mode: AuthMode }) {
  const [locale, setLocale] = useState<Locale>("fr");
  const t = copy[locale];
  const intro = t.intro[mode];

  useEffect(() => {
    const savedLocale = window.localStorage.getItem("skkup-language");
    if (savedLocale === "en") setLocale("en");
    document.documentElement.lang = savedLocale === "en" ? "en" : "fr";
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <main className="auth-page" lang={locale}>
      <PublicAuthHeader mode={mode} locale={locale} setLocale={setLocale} />

      <div className="auth-layout">
        <section className="auth-intro" aria-labelledby="auth-intro-title">
          <p className="auth-kicker">{intro.kicker}</p>
          <h1 id="auth-intro-title">
            {intro.title}
            <br />
            <span>{intro.accent}</span>
          </h1>
          <p className="auth-description">{intro.description}</p>
          <ul className="auth-benefits">
            <li>
              <Image className="auth-benefit-image" src="/assets/auth/points.png" alt="" aria-hidden width={28} height={28} />
              {intro.benefitOne}
            </li>
            <li>
              <Image className="auth-benefit-image" src="/assets/auth/ticket.png" alt="" aria-hidden width={28} height={28} />
              {intro.benefitTwo}
            </li>
          </ul>
        </section>

        <AuthForm mode={mode} locale={locale} />
      </div>
    </main>
  );
}

type AuthProfile = { pseudo: string; email: string; role: string };

function PublicAuthHeader({
  mode,
  locale,
  setLocale,
}: {
  mode: AuthMode;
  locale: Locale;
  setLocale: (locale: Locale) => void;
}) {
  const router = useRouter();
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [profile, setProfile] = useState<AuthProfile | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState(false);
  const t = copy[locale];

  useEffect(() => {
    let active = true;
    fetch(`${apiBase}/auth/session`, { credentials: "include" })
      .then((response) => response.json())
      .then((payload: unknown) => {
        if (!active || !payload || typeof payload !== "object") return;
        const session = payload as { authentifie?: unknown; profil?: unknown };
        if (session.authentifie !== true || !session.profil || typeof session.profil !== "object") return;
        const candidate = session.profil as Record<string, unknown>;
        if (typeof candidate.pseudo === "string" && typeof candidate.email === "string" && typeof candidate.role === "string") {
          setProfile({ pseudo: candidate.pseudo, email: candidate.email, role: candidate.role });
        }
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    menuRef.current?.querySelector<HTMLElement>("[role='menuitem'], [role='menuitemradio'][tabindex='0']")?.focus();
    function closeOnOutside(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setMenuOpen(false);
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
        requestAnimationFrame(() => triggerRef.current?.focus());
      }
      if (event.key === "Tab") {
        const controls = Array.from(menuRef.current?.querySelectorAll<HTMLElement>("[role='menuitem'], [role='menuitemradio'][tabindex='0']") ?? []);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    }
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [menuOpen]);

  async function logout() {
    setLoggingOut(true);
    setLogoutError(false);
    try {
      const response = await fetch(`${apiBase}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) throw new Error("Logout failed");
      router.push("/");
      router.refresh();
    } catch {
      setLogoutError(true);
    } finally {
      setLoggingOut(false);
    }
  }

  function chooseLocale(next: Locale) {
    setLocale(next);
    window.localStorage.setItem("skkup-language", next);
    document.documentElement.lang = next;
  }

  const otherMode = mode === "connexion" ? "inscription" : "connexion";
  const accountLabel = locale === "en" ? "Account actions" : "Actions du compte";

  return (
    <header className="auth-header">
      <Link className="auth-wordmark" href="/" aria-label="Accueil Skkup">
        <Image
          src="/assets/auth/skkup-wordmark-transparent.png"
          alt="Skkup"
          width={190}
          height={70}
          priority
        />
      </Link>
      <nav className="auth-header-actions">
        {profile ? (
          <div className="auth-account" ref={menuRef}>
            <button
              ref={triggerRef}
              type="button"
              className="auth-account-trigger"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              aria-label={`${locale === "en" ? "Open the menu for" : "Ouvrir le menu de"} ${profile.pseudo}`}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span className="auth-account-avatar" aria-hidden="true">{profile.pseudo.trim().charAt(0).toUpperCase()}</span>
              <span>{profile.pseudo}</span>
              <span aria-hidden="true">⌄</span>
            </button>
            {menuOpen && (
              <div className="auth-account-menu" role="menu" aria-label={`${accountLabel} ${profile.pseudo}`}>
                <p className="auth-account-eyebrow">{locale === "en" ? "Signed in as" : "Connecté en tant que"}</p>
                <p className="auth-account-email">{profile.email}</p>
                <div className="auth-account-divider" />
                <div className="auth-account-languages" role="group" aria-label={locale === "en" ? "Language" : "Langue"}>
                  {(["fr", "en"] as const).map((code) => (
                    <button
                      key={code}
                      type="button"
                      role="menuitemradio"
                      aria-checked={locale === code}
                      tabIndex={locale === code ? 0 : -1}
                      data-account-language={code}
                      onClick={() => chooseLocale(code)}
                      onKeyDown={(event) => {
                        if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
                        event.preventDefault();
                        const next: Locale = code === "fr" ? "en" : "fr";
                        chooseLocale(next);
                        requestAnimationFrame(() => menuRef.current?.querySelector<HTMLButtonElement>(`[data-account-language='${next}']`)?.focus());
                      }}
                    >
                      {code.toUpperCase()}
                    </button>
                  ))}
                </div>
                <div className="auth-account-divider" />
                <Link href="/dashboard" role="menuitem" onClick={() => setMenuOpen(false)}>{t.dashboard}</Link>
                {profile.role === "ADMIN" && <Link href="/admin" role="menuitem" onClick={() => setMenuOpen(false)}>Administration</Link>}
                <button type="button" role="menuitem" disabled={loggingOut} onClick={() => void logout()}>
                  {loggingOut ? (locale === "en" ? "Logging out..." : "Déconnexion...") : locale === "en" ? "Log out" : "Déconnexion"}
                </button>
                {logoutError && <p className="auth-account-error" role="alert">{t.form.genericError}</p>}
              </div>
            )}
          </div>
        ) : (
          <Link className="auth-header-link" href={`/${otherMode}`}>{t.headerAction[mode]}</Link>
        )}
      </nav>
    </header>
  );
}

function AuthForm({ mode, locale }: { mode: AuthMode; locale: Locale }) {
  const router = useRouter();
  const termsDialogRef = useRef<HTMLElement>(null);
  const registrationStartRef = useRef<HTMLInputElement>(null);
  const t = copy[locale].form;
  const current = t[mode];
  const [pseudo, setPseudo] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [readTerms, setReadTerms] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const termsDialogOpen = mode === "inscription" && !acceptedTerms;
  const passwordChecks = useMemo(
    () => [
      password.length >= 12,
      /[A-Z]/.test(password),
      /[a-z]/.test(password),
      /\d/.test(password),
      /[^A-Za-z0-9]/.test(password),
    ],
    [password],
  );
  const passwordValid = passwordChecks.every(Boolean);

  useEffect(() => {
    if (!termsDialogOpen) return;
    const dialog = termsDialogRef.current;
    if (!dialog) return;
    const activeDialog: HTMLElement = dialog;

    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    const page = dialog.closest(".auth-page");
    const background = Array.from(
      page?.querySelectorAll<HTMLElement>(
        ".auth-header, .auth-intro, .auth-card > :not(.auth-terms-backdrop)",
      ) ?? [],
    );
    const previousInert = background.map((element) => element.inert);
    background.forEach((element) => { element.inert = true; });

    dialog.querySelector<HTMLInputElement>("input[type='checkbox']")?.focus();

    function focusableElements() {
      return Array.from(
        activeDialog.querySelectorAll<HTMLElement>(
          "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
        ),
      ).filter((element) => !element.hidden && element.getAttribute("aria-hidden") !== "true");
    }

    function keepTabInDialog(event: KeyboardEvent) {
      if (event.key !== "Tab") return;
      const focusable = focusableElements();
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (!activeDialog.contains(active)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      } else if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", keepTabInDialog, true);
    return () => {
      document.removeEventListener("keydown", keepTabInDialog, true);
      background.forEach((element, index) => { element.inert = previousInert[index]; });
      if (previousFocus?.isConnected && previousFocus !== document.body) previousFocus.focus();
    };
  }, [termsDialogOpen]);

  useEffect(() => {
    if (mode === "inscription" && acceptedTerms) registrationStartRef.current?.focus();
  }, [acceptedTerms, mode]);

  function refuseTerms() {
    router.push("/");
  }

  function acceptTerms() {
    setAcceptedTerms(true);
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (mode === "inscription" && password !== confirmation) {
      setError(t.mismatch);
      return;
    }
    if (mode === "inscription" && !passwordValid) {
      setError(t.passwordInvalid);
      return;
    }
    if (mode === "inscription" && !acceptedTerms) {
      setError(t.ruleAcceptanceRequired);
      return;
    }

    setSubmitting(true);
    try {
      const endpoint = mode === "connexion" ? "/auth/login" : "/auth/register";
      const body =
        mode === "connexion"
          ? { email, motDePasse: password }
          : { email, motDePasse: password, pseudo, accepteReglement: true };
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const payload: unknown = await response.json().catch(() => null);
        const message = apiErrorMessage(payload);
        throw new Error(message ?? t.genericError);
      }

      router.push("/dashboard");
      router.refresh();
    } catch (cause) {
      setError(cause instanceof TypeError ? t.networkError : cause instanceof Error ? cause.message : t.genericError);
      setSubmitting(false);
    }
  }

  const rulesText = locale === "fr" ? reglementMarkdown : reglementMarkdownEn;

  return (
    <section className="auth-card" aria-labelledby="auth-form-title">
      <h2 id="auth-form-title">{current.title}</h2>
      <p className="auth-card-subtitle">{current.subtitle}</p>

      {mode === "inscription" && !acceptedTerms && (
        <div className="auth-terms-backdrop" role="presentation">
          <section
            ref={termsDialogRef}
            className="auth-terms-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="auth-terms-title"
            aria-describedby="auth-terms-description"
            onKeyDown={(event) => {
              if (event.key === "Escape") refuseTerms();
            }}
          >
            <div className="auth-terms-heading">
              <div>
                <h2 id="auth-terms-title">{t.rulesTitle}</h2>
                <p id="auth-terms-description">{t.rulesDescription}</p>
              </div>
              <button
                type="button"
                className="auth-dialog-close"
                aria-label={t.closeRules}
                onClick={refuseTerms}
              >
                <Image src="/assets/auth/close.png" alt="" aria-hidden width={16} height={16} />
              </button>
            </div>
            <div className="auth-terms-scroll">
              <RuleText text={rulesText} locale={locale} />
            </div>
            <div className="auth-terms-actions">
              <label className="auth-checkbox-label" htmlFor="acceptTerms">
                <input
                  id="acceptTerms"
                  name="acceptTerms"
                  type="checkbox"
                  checked={readTerms}
                  onChange={(event) => setReadTerms(event.target.checked)}
                  autoFocus
                />
                <span>{t.acceptRules}</span>
              </label>
              <button
                type="button"
                className="auth-submit"
                disabled={!readTerms}
                onClick={acceptTerms}
              >
                {t.acceptAction}
              </button>
              <button type="button" className="auth-refuse" onClick={refuseTerms}>
                {t.refuseAction}
              </button>
            </div>
          </section>
        </div>
      )}

      {(mode === "connexion" || acceptedTerms) && (
        <form className="auth-form" onSubmit={submit}>
          {mode === "inscription" && (
            <label className="auth-field">
              <span>{t.pseudo}</span>
              <input
                ref={registrationStartRef}
                name="pseudo"
                type="text"
                autoComplete="username"
                minLength={2}
                required
                value={pseudo}
                onChange={(event) => setPseudo(event.target.value)}
              />
            </label>
          )}

          <label className="auth-field">
            <span>{t.email}</span>
            <input
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="auth-field">
            <span>{t.password}</span>
            <input
              name="password"
              type="password"
              autoComplete={mode === "inscription" ? "new-password" : "current-password"}
              minLength={mode === "inscription" ? 12 : undefined}
              pattern={mode === "inscription" ? "(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{12,}" : undefined}
              aria-describedby={mode === "inscription" ? "auth-password-rules" : undefined}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {mode === "inscription" && (
              <span className="auth-password-hint" id="auth-password-rules">
                <span className="auth-password-hint-title">{t.passwordRequirements}</span>
                <ul aria-live="polite">
                  {t.passwordRules.map((rule, index) => (
                    <li className={passwordChecks[index] ? "is-valid" : ""} key={rule}>
                      <span aria-hidden="true">{passwordChecks[index] ? "✓" : "○"}</span>
                      {rule}
                    </li>
                  ))}
                </ul>
                {passwordValid && <span className="auth-password-valid">{t.passwordValid}</span>}
              </span>
            )}
          </label>

          {mode === "inscription" && (
            <label className="auth-field">
              <span>{t.confirmPassword}</span>
              <input
                name="confirmationMotDePasse"
                type="password"
                autoComplete="new-password"
                minLength={12}
                required
                value={confirmation}
                aria-invalid={confirmation.length > 0 && password !== confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
              />
              {confirmation.length > 0 && password !== confirmation && (
                <span className="auth-inline-error">{t.mismatch}</span>
              )}
            </label>
          )}

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting ? current.submitting : current.submit}
          </button>
        </form>
      )}

      <p className="auth-switch">
        {current.invite}{" "}
        <Link href={`/${mode === "connexion" ? "inscription" : "connexion"}`}>
          {current.switch}
        </Link>
      </p>
    </section>
  );
}

function apiErrorMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const record = payload as Record<string, unknown>;
  const detail = record.detail ?? record.message;
  return typeof detail === "string" ? detail : null;
}
