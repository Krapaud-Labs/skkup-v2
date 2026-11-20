# Skkup V2

Nouvelle base applicative pour la plateforme Skkup. L’API V2 inclut l’authentification membre, la progression Viewer et l’administration des tirages (#5, #6 et #8 fusionnés dans `dev`). Le lot #9, consacré aux tickets à gratter `CLASSIC`/`PREMIUM` et aux participations distinctes aux tirages, est en cours de livraison vers `dev`.

## Périmètre

Le projet vise à préserver les fonctions Viewer, Admin, publiques et d'extension présentes en V1, avec une refonte des dashboards et une nouvelle base technique. La vitrine et l'authentification doivent conserver leur rendu visible. Le détail des décisions, du barème et des vérifications restantes figure dans [la documentation](docs/README.md).

La couverture statique vérifiable de la référence V1 au commit `fcc4767f3ece9efc069d1a1c413942067cb89c93` comprend 27 pages applicatives, 81 routes HTTP et 58 entrées de médias runtime avec chemins, formats, dimensions et empreintes SHA-256 consignés. La méthode de comptage est reproductible depuis ce commit et l’inventaire média est détaillé dans [la readiness de conception](docs/design/design-readiness.md) et [le manifeste des médias](docs/design/media-inventory.md). Cette analyse statique ne valide ni le comportement réellement déployé, ni l’exécution des tests, ni la parité visuelle; les formes de réponse ou autorisations non établies restent signalées comme inconnues.

## Scaffold technique

- API : FastAPI 0.163.1 sur Uvicorn 0.54.0, avec contrôles de santé et routes
  d’authentification `/auth/register`, `/auth/login`, `/auth/session`,
  `/auth/logout` et `/auth/password`, ainsi que les services Viewer `/me`,
  `/me/points`, `/me/points/history`, `/me/reward-tickets` et
  `/me/daily-checkin`.
- Interface : Next.js 16.4.6 avec React 19.3.0. Les pages `/connexion` et
  `/inscription` présentent les formulaires d'authentification; l'inscription
  ouvre le règlement du jeu dans une modale avant le consentement. La route
  `/dashboard` présente, après connexion, le solde Viewer, sa série, ses tickets,
  sa progression et son activité récente. L’historique et le compte s’ouvrent
  dans des modales accessibles.
- Base de données : PostgreSQL 18.6.
- Migrations : Alembic 1.20.1 et SQLAlchemy 2.0.57, avec Psycopg 3.3.9.
- Runtime du conteneur : Python 3.13.18.
- Runtime web : Node.js 26.13.1.
- Environnement local : Docker Compose, avec trois services applicatifs et
  une migration de démarrage.
- CI : GitHub Actions sur les pull requests vers `dev`.

Compose initialise une base locale dédiée et vide, applique les migrations
Alembic, puis démarre l'API et l'interface web. Le schéma comprend les comptes
Viewer, les sessions web révocables, le ledger de points, les séries de
connexion et l’inventaire des tickets. Les routes Viewer requièrent une session
authentifiée; le check-in quotidien est idempotent. Le changement de mot de
passe incrémente `session_version` et
révoque les sessions web; la révocation des appairages d’extension et des
sessions de visionnage reste à intégrer avec le lot #7. L’authentification est
un premier lot de développement et ne constitue pas une configuration de
production.

Les écrans Auth reprennent la structure de référence des pages Connexion et
Inscription et utilisent les ressources suivies sous
`frontend/public/assets/auth/` : `skkup-wordmark-transparent.png`, `points.png`,
`ticket.png` et `close.png`. Le dialogue de règlement place le focus sur sa
case d'acceptation, confine Tab et Maj+Tab, rend le contenu arrière inerte et
restitue le focus au champ pseudo après acceptation. Les pages Auth gardent un
défilement vertical utilisable sur petit écran sans débordement horizontal.
QA a comparé des captures Chromium headless V1/V2 desktop, mobile et inscription.
Les écarts visuels résiduels sont estimés à environ 10–20 px sur mobile et
5 px sur la modale selon les vues. Aucun diff quantitatif n'a été produit; le
pixel-perfect et l'identité à 100 % ne sont pas revendiqués. Sur la modale
mobile, le document mesurait 1 019 px pour un viewport de 844 px; le CTA à
y=920 est devenu entièrement visible après `scrollY=175`. Vingt pressions Tab
sont restées dans la modale sans soumettre le formulaire. Les listes du
règlement restent sans puces visibles comme dans la capture V1. Une scrollbar
violette est encore visible dans la modale V2 alors qu'elle ne l'est pas sur la
capture V1. La route Dashboard existe désormais et est liée à l’API de
progression Viewer. La parité fonctionnelle complète reste à vérifier.

Le Dashboard Viewer/Admin partage un shell et reprend la vitrine : surfaces
bleu nuit, accents violet et cyan, dégradés et halos discrets. Sa navigation
reste compacte; les détails et éditions Admin, comme l’historique Viewer,
s’ouvrent dans des modales, tandis que les listes longues défilent dans leur
propre région. Les layouts Viewer et Admin Raffles/Lots ont été vérifiés avant
leur fusion dans `dev` via #15 et #16. Le lot #9 ajoute les parcours Viewer de
grattage et de participation ainsi que l’exécution Admin des tirages; sa
validation responsive et clavier est en cours.

## Prérequis

Installer Docker Desktop ou Docker Engine avec Docker Compose v2. Les services
locaux utilisent par défaut le port `5433` pour PostgreSQL, `8000` pour l'API
et `3010` pour l'interface sur `127.0.0.1`; vérifie qu'ils sont libres. Les
variables `DB_HOST_PORT`, `API_HOST_PORT` et `WEB_PORT` permettent de choisir
d'autres ports hôtes.

## Démarrer la base locale

Prépare une configuration locale ignorée par Git et une clé aléatoire qui
n’est pas enregistrée dans le dépôt :

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Copie la valeur générée dans `AUTH_TOKEN_SECRET` de ton `.env` local. Garde
`COOKIE_SECURE=false` uniquement pour le HTTP local. La valeur
`AUTH_ALLOWED_ORIGINS` de l’exemple autorise `http://localhost:3010` et
`http://127.0.0.1:3010`.
Pour que le cookie `SameSite=Lax` et l’API par défaut restent sur le même site,
ouvre l’interface à `http://localhost:3010`; le frontend appelle
`http://localhost:8000` et envoie les credentials du cookie. Les deux origines
sont autorisées par CORS, mais mélanger `localhost` et `127.0.0.1` entre
l’interface et l’API peut empêcher l’envoi du cookie.

Pour un environnement HTTPS, configure `COOKIE_SECURE=true`, garde une clé
privée d’au moins 32 octets dans l’environnement et définis exactement les
origines autorisées. Aucun secret ne doit être ajouté à Git.

```bash
docker compose up --build -d
docker compose ps --all
```

Compose attend le healthcheck `pg_isready` de PostgreSQL avant de lancer
Alembic, puis attend la réussite de la migration avant de démarrer l'API.
L'API passe healthy après une requête `SELECT 1` réussie; l'interface passe
healthy quand sa page répond. Le conteneur `migrate` s'arrête avec le code 0
lorsque la révision `0003_viewer_points` a été appliquée. Pour vérifier la
révision :

```bash
docker compose run --rm migrate alembic -c alembic.ini current
```

Arrêter les services en conservant la base locale :

```bash
docker compose down
```

## Contrôles locaux

Installer les dépendances de développement :

```bash
uv sync --project backend --locked --extra dev
npm ci --ignore-scripts --no-audit --no-fund --prefix frontend
```

Les contrôles ciblés suivants sont disponibles :

```bash
uv run --project backend --locked --extra dev ruff check backend/app backend/migrations backend/tests
uv run --project backend --locked python -m compileall -q backend/app backend/migrations
PYTHONPATH=backend uv run --project backend --locked --no-sync python -m unittest discover -s backend/tests -p 'test_*.py'
npm --prefix frontend run build
docker compose config --quiet
```

QA rapporte cinq tests Auth réussis après le correctif TZ : quatre tests de
contrat exécutent directement l'ASGI FastAPI avec `unittest` et SQLite en
mémoire, et un test unitaire vérifie le rollover au changement de jour civil.
Les tests de contrat couvrent validation, consentement, cookie, profil Viewer,
erreurs de connexion, révocation à la déconnexion et au changement de mot de
passe, origines et préflight CORS. Ruff passe sur `backend/app`,
`backend/migrations` et `backend/tests`. Les captures Chromium headless
desktop/mobile/inscription ont été comparées à V1; les écarts restent estimatifs
et aucun diff quantitatif n'a été produit. La comparaison ne prouve pas une
identité pixel à pixel ni une validation complète des formulaires ou parcours.
La migration Docker/PostgreSQL n'a pas été vérifiée localement car le socket
Docker a refusé l'accès. La CI inclut le build et le smoke test Compose, sans
résultat CI revendiqué ici.

Réinitialiser la base locale en supprimant son volume et toutes ses données :

```bash
docker compose down --volumes
```

La variable `POSTGRES_PASSWORD` de `.env.example` est un mot de passe de
démonstration réservé à la base locale. Ne la réutilise jamais dans un
environnement partagé ou de production. Les migrations s'appliquent via
`alembic upgrade head`; leur retour arrière de développement est
`alembic downgrade base`, qui efface les tables locales `users` et
`auth_sessions` ajoutées par l’authentification ainsi que la ligne de version.
Alembic conserve sa table interne `alembic_version`. Ne lance cette commande
que si tu acceptes d’effacer les données locales.

Les commandes reproductibles du socle sont aussi disponibles localement :

```bash
bash .github/scripts/preflight.sh
bash .github/scripts/security-check.sh
uv sync --project backend --locked --extra dev && npm ci --ignore-scripts --no-audit --no-fund --prefix frontend
uv run --project backend --locked --extra dev ruff check backend/app backend/migrations
npm --prefix frontend run build && docker compose build
bash .github/scripts/verify-scaffold.sh
```

Le preflight vérifie la présence et la cohérence des manifestes et lockfiles
Python/JavaScript. Le contrôle sécurité refuse les fichiers `.env` sensibles
suivis par Git et recherche les marqueurs PEM de clés privées dans les fichiers
suivis par Git, hors répertoires générés. Les fichiers non suivis ne sont pas
analysés localement avant leur ajout à Git; les fichiers de plus de 2 Mo sont
ignorés. Il ne remplace
pas un scanner de vulnérabilités, un contrôle exhaustif de secrets, ni une
revue de dépendances. Le smoke test construit et démarre les trois services sur
un nom de projet Compose et des ports hôtes temporaires uniques; il teste les
healthchecks et le cycle Alembic, puis supprime uniquement son projet et son
volume jetable avec `down --volumes`. Il requiert Docker Compose et peut prendre
le temps d'un build initial. La boucle de readiness a une échéance de 180
secondes; chaque sonde est elle aussi bornée afin que le smoke ne reste pas
bloqué sur un service qui ne répond plus.

La CI lance ces contrôles sur une pull request vers `dev` ou manuellement avec
`workflow_dispatch`. `concurrency` annule un ancien run du même workflow et de
la même ref quand un nouveau démarre. Elle préflight les manifestes, exécute le
contrôle sécurité, installe les dépendances verrouillées, lance le lint, les
tests Auth ASGI, le build et le smoke test isolé. Il n'existe pas de déclencheur
de push ni de publication.

CI utilise uniquement le runner GitHub-hosted standard `ubuntu-latest`. Le
dépôt est public selon D-01; GitHub indique que ses runners standards sont
gratuits et sans limite de minutes pour les dépôts publics ([documentation
GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)).
Aucun runner self-hosted, runner supérieur, secret ou service payant n'est
configuré ni requis.

Les documents canoniques commencent dans [docs/README.md](docs/README.md).

## Assets des tickets à gratter

Les visuels fournis pour les tickets à gratter sont disponibles comme ressources publiques du frontend :

- Ticket à gratter `CLASSIC` : `/images/tickets/scratch-classic.png` (PNG RGBA, 1774 × 887 px).
- Ticket à gratter `PREMIUM` : `/images/tickets/scratch-premium.png` (PNG RGBA, 1774 × 887 px).

Ils sont servis tels que fournis, avec leur canal alpha. Le frontend peut les afficher dans un élément image responsive, en conservant le ratio d’origine (`width: 100%; height: auto`). Ces fichiers sont des éléments visuels uniquement : le parcours de grattage, les probabilités et l’attribution des récompenses ne sont pas implémentés par cet ajout.

Dans le barème D-07 et l’inventaire Viewer, `CLASSIC` et `PREMIUM`
désignent exclusivement des tickets à gratter, jamais des tickets de
participation à un tirage. Une participation à un tirage est une donnée
distincte, stockée dans `raffleTicket`. Dans V1, le résultat de grattage
« ticket » pouvait créer une participation lorsqu’un tirage était ouvert. La
décision D-16/D-20 remplace ce comportement en V2: ce résultat attribue un
ticket à gratter `CLASSIC`, avec le fallback en points si aucun tirage n’est
ouvert. `reward_tickets` contient les tickets à gratter; seul le parcours
explicite de participation au concours crée une entrée `raffleTicket`.
« Accès au concours » est un résultat distinct du ticket à gratter.

## Limites actuelles

Le produit reste en construction et aucune procédure de déploiement n’est fournie. Le cadrage n'autorise aucun accès ou changement à la production, aucune migration des données V1 ni création de secret. Le lot #8, qui configure les tirages et leurs lots côté Admin, est fusionné dans `dev`. Le lot #9 ajoute séparément l’exécution des tirages, leurs participations, leurs résultats et l’expérience de grattage; cette livraison est en cours et n’active pas le produit publiquement. La reprise des données V1 reste à construire ou à valider dans ses lots dédiés. Le cadrage interdit la copie d'actifs de la V1 ou de la production sans autorisation documentée; les deux tickets ci-dessus ont été fournis par le propriétaire du projet et constituent l'unique exception ajoutée ici. La stratégie de données part d'une base V2 vide; les données de production V1 restent à inventorier avant toute décision de reprise. L’inventaire statique seul ne valide pas le comportement déployé, la parité visuelle complète, ni la publication des routes ou médias.

Le cadrage de conception est `approved` depuis le 2026-11-16, après revue Produit, QA, audit indépendant et scan des marqueurs. Cette approbation autorise la planification des lots; elle ne certifie pas une application V2 ni l'exécution de tests ou contrôles visuels. Les lots doivent conserver leurs préconditions : comparaison de rendus et responsive/contrastes mesurés, tests V2, tests négatifs d’accès Admin côté serveur, preuve de droits avant copie de médias et décisions données/production/publication avant release.

## Suivi

Le suivi choisi est GitHub Projects, projet « Skkup V2 ». Le Project d'organisation a été créé et relu; sa vue par défaut montre `Todo`, `In Progress` et `Done`. Les issues MVP/Post-MVP #3 à #9 sont créées et relues. Les statuts actuels sont visibles dans le Project; P0 est mappé sur Priority `Urgent` et P1 sur `High`. Voir [l'état du suivi et les liens des issues](docs/project-management/github-project.md).
