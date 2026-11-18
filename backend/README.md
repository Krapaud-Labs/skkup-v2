# Backend V2

FastAPI service for the Skkup V2 API. Database schema changes are applied with
Alembic; the service does not create tables automatically.

## Member authentication

The initial auth slice preserves the V1 route and response shapes:

- `POST /auth/register`: `{ "email", "pseudo", "motDePasse", "accepteReglement" }`, returns `201 { "pseudo" }` and sets the session cookie.
- `POST /auth/login`: `{ "email", "motDePasse" }`, returns `200 { "pseudo" }` and sets the session cookie.
- `GET /auth/session`: returns `{ "authentifie": false, "profil": null }` when anonymous, otherwise the public account profile.
- `POST /auth/logout`: returns `204`, revokes the current session when valid and clears the cookie even if it is invalid.
- `PATCH /auth/password`: `{ "ancienMotDePasse", "nouveauMotDePasse" }`, returns `204`, changes the hash and revokes all web sessions.

Registration requires at least 12 characters, lowercase, uppercase, a digit,
and a non-alphanumeric character. Password changes follow the V1 DTO, which
requires 12 characters, lowercase, uppercase and a digit but does not require a
symbol. Registration requires explicit terms acceptance. Accounts are created
as `VIEWER`; the client cannot choose a role. Password recovery and email
verification are not implemented because no accepted email workflow exists.
Invalid request bodies return HTTP 400 with safe field-relevant French
messages; request values and passwords are never echoed. Exact V1 validator
wording remains subject to source-parity review.

Passwords use Python's built-in scrypt implementation to avoid adding a
runtime package to the minimal scaffold. This is a reversible V2 baseline;
existing V1 password hashes are not imported or migrated. Web sessions use the
V1-compatible signed HS256 token shape and a database `auth_sessions` row so
logout, password changes and expiry can be enforced immediately by the API.
The token's `jourConnexion` is compared to the Europe/Paris civil day; it
becomes invalid at midnight in that timezone even if its 24-hour `exp` has not
elapsed, matching the civil-day check in `JwtStrategy.validate` in V1 commit
`fcc4767f3ece9efc069d1a1c413942067cb89c93`. V1's published regulation names
Europe/Paris, but its versioned Compose and Docker configuration do not set a
server timezone, so the historical runtime timezone cannot be proven from the
repository. V2 explicitly sets `TZ=Europe/Paris` for the API and includes
`tzdata` in the runtime image. Keep all API workers on this timezone. The
signing secret is never stored in the repository.

## Configuration

The API requires the existing PostgreSQL variables `DB_HOST`, `POSTGRES_DB`,
`POSTGRES_USER` and `POSTGRES_PASSWORD`. Authentication also requires
`AUTH_TOKEN_SECRET` with at least 32 bytes. Configure `AUTH_ALLOWED_ORIGINS`
as a comma-separated exact origin list; the development default is
`http://localhost:3010,http://127.0.0.1:3010,http://localhost:3000,http://127.0.0.1:3000`
to cover the repository's local web port and common direct development ports.
Browser state-changing auth requests require a matching `Origin`, and CORS
allows credentials only for the configured origins.

Generate a local-only signing key in the shell before starting the API, and
pass it into the process environment; do not commit it:

```bash
export AUTH_TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

Compose requires this variable and passes it to the API container. It also
passes `AUTH_ALLOWED_ORIGINS` and explicit `COOKIE_SECURE` settings. For a
local HTTP session, use the committed `.env.example` as a template and set
`COOKIE_SECURE=false`; do not use that setting behind a public HTTP endpoint.
The auth client sends `credentials: "include"`. Browse locally at
`http://localhost:3010` so its default API origin `http://localhost:8000`
remains same-site for the Lax cookie. The `127.0.0.1:3010` origin is allowed
for CORS as requested, but the current frontend default still calls
`localhost:8000`; using the two different host spellings can cause browsers to
withhold a Lax cookie. A future client/runtime change must choose a matching
host on both sides before claiming both URL variants work end to end.

`COOKIE_SECURE` defaults to `true`, setting `Secure`, `HttpOnly`,
`SameSite=Lax`, `Path=/`, and the `__Host-vr_session` cookie name. For local
HTTP development only, set `COOKIE_SECURE=false`; this uses `vr_session`
because browsers reject `__Host-` cookies without `Secure`.

Authentication throttles are in-process and keyed by the direct client
address: 5 registrations/hour, 10 login attempts/minute, and 3 password
changes/hour. This protects a single service process without adding Redis or
another service. It is not shared across workers, containers, or restarts; a
multi-worker/public deployment needs a shared rate limiter before exposure.

## Viewer points and daily progression

The issue #6 backend routes are authenticated from the current session cookie;
they never accept a user ID from a request body or query:

- `GET /me` preserves the V1 profile response shape.
- `GET /me/points` returns the points balance, current and maximum streak, next
  documented streak milestone, and counts of available CLASSIC/PREMIUM reward
  tickets.
- `GET /me/points/history?page=1&limit=20` returns the V1 pagination envelope
  and point transaction field names, filtered to the authenticated Viewer.
- `GET /me/reward-tickets?page=1&limit=20` lists unassigned reward tickets.
- `POST /me/daily-checkin` uses the session identity and requires an allowlisted
  `Origin`. It returns a stable replay response for another request on the same
  Europe/Paris civil day.

The accepted D-14 rule replaces the V1 direct +5 check-in credit with one
CLASSIC reward ticket, so a daily check-in writes no points ledger entry. D-15
adds +1 CLASSIC on streak day 3, +2 CLASSIC on day 7, +2 CLASSIC and +1 PREMIUM
on day 14, and +2 CLASSIC and +2 PREMIUM on day 30. These awards are in
addition to the daily CLASSIC ticket. The V1 streak scratch-card grants at
days 3, 7, 14 and 30 are recorded atomically as available grants. V1's
preselected TICKET result on card grants at multiples of 10 after day 30 is
preserved as grant metadata, without adding D-07 tickets.
No scratch outcome is selected in this lot. D-16 is enforced by the shared
ticket-award service, which categorizes a future scratch-card ticket as
CLASSIC. Ticket reveal, random selection and conversion to a raffle entry are
reserved for issue #9. Reward tickets are inventory records distinct from
raffle entries; this lot does not consume them or implement purchases.

Point changes use a transaction ledger with signed amounts, a recorded
post-change balance, and a per-user idempotency key. Zero-point activity rows
remain representable for V1-compatible scratch outcomes. The user balance
update and ledger row are written in one transaction; negative balances are
rejected, and no global or daily point cap is introduced. The ledger and ticket
inventory are separate so ticket awards cannot be mistaken for points.

For idempotent daily check-in, V2 uses a unique `(user_id, local_day)` event,
locks the user row during the operation, and commits the streak, card grant and
ticket awards together. A repeated request returns the stored ticket and card
IDs without another reward. This differs from V1's duplicate-check-in HTTP 409
response but keeps the award effect unique and makes retries safe. The
`scratch_card_grants` table records only entitlements, not scratch results or
animation state; issue #9 owns those mechanics.

## Migration

After setting the database environment, apply the schema with the repository's
Alembic configuration. Migration `0002_member_auth` creates the new `users`
and `auth_sessions` tables; `0003_viewer_points` adds the point ledger,
idempotent daily check-ins, scratch-card grant events and reward-ticket
inventory. These migrations build on the empty V2 baseline and do not import
or modify V1 or production data.

## Backend contract checks

Run the dependency-free API contract checks from the repository root:

```bash
PYTHONPATH=backend uv run --project backend --locked --no-sync python -m unittest discover -s backend/tests -p 'test_*.py'
```

These checks drive the FastAPI ASGI app and points service with in-memory
SQLite. They cover request validation, registration and consent, session
cookies, the Viewer profile, login errors, logout and password-change
revocation, exact Origin checks, credentialed CORS preflight, daily reward
idempotence, D-14/D-15 categories, D-16 scratch-ticket categorization, point
ledger/balance coherence, rollback and user/day uniqueness. They do not replace
a PostgreSQL concurrency/migration test or browser/UI and visual verification.

The issue #5 and #6 backend suites run through the command above. Ruff over
`backend/app`, `backend/migrations` and `backend/tests` is required. SQLite
checks cover rollback and the unique same-day constraint; actual parallel
PostgreSQL locking and Compose migration execution remain deployment/CI checks.
Form UI, navigation, keyboard behavior and screenshots remain outside these
API contract checks.

## Current limits

- Password change increments `session_version` and revokes all V2 web sessions.
  V1 also revokes active extension pairings, unused pairing tokens and active
  watch sessions. V2 has not implemented those tables yet, so that effect is
  not complete before issue #7. Every future extension credential must include
  the account's `session_version` epoch and validate it server-side on every
  request. Pairing revocation and watch-session invalidation remain explicit
  #7 work; no complete extension invalidation is claimed in this lot.
- SameSite Lax plus exact Origin validation is the initial CSRF defense. Proxy
  trust, production origin setup, and frontend credentialed-fetch behavior
  must be verified in the deployment and browser integration work.
- The login/register email validator is a small syntactic check and is not a
  complete RFC mailbox parser. The accepted V1 field and message behavior
  should be verified before claiming full validation parity.
- Session expiration is 24 hours, matching the V1 cookie and token lifetime.
