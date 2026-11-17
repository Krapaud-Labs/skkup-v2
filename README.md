# Skkup V2

Nouvelle base applicative publique pour la plateforme Skkup. Le dépôt contient le cadrage, les documents de conception et le scaffold technique V2; les fonctionnalités produit ne sont pas encore implémentées.

## Périmètre

Le projet vise à préserver les fonctions Viewer, Admin, publiques et d'extension présentes en V1, avec une refonte des dashboards et une nouvelle base technique. La vitrine et l'authentification doivent conserver leur rendu visible. Le détail des décisions, du barème et des vérifications restantes figure dans [la documentation](docs/README.md).

La couverture statique vérifiable de la référence V1 au commit `fcc4767f3ece9efc069d1a1c413942067cb89c93` comprend 27 pages applicatives, 81 routes HTTP et 58 entrées de médias runtime avec chemins, formats, dimensions et empreintes SHA-256 consignés. La méthode de comptage est reproductible depuis ce commit et l’inventaire média est détaillé dans [la readiness de conception](docs/design/design-readiness.md) et [le manifeste des médias](docs/design/media-inventory.md). Cette analyse statique ne valide ni le comportement réellement déployé, ni l’exécution des tests, ni la parité visuelle; les formes de réponse ou autorisations non établies restent signalées comme inconnues.

## Scaffold technique

- API : FastAPI 0.163.1 sur Uvicorn 0.54.0, limitée pour l'instant aux
  contrôles de santé `/health/live` et `/health/ready`.
- Interface : Next.js 16.4.6 avec React 19.3.0, page d'accueil technique
  minimale.
- Base de données : PostgreSQL 18.6.
- Migrations : Alembic 1.20.1 et SQLAlchemy 2.0.57, avec Psycopg 3.3.9.
- Runtime du conteneur : Python 3.13.18.
- Runtime web : Node.js 26.13.1.
- Environnement local : Docker Compose, avec trois services applicatifs et
  une migration de démarrage.
- CI : GitHub Actions sur les pull requests vers `dev`.

Le premier scaffold initialise une base locale dédiée et vide, démarre l'API
et l'interface web minimales, puis exécute la baseline Alembic. Les seules
routes API sont les contrôles techniques de santé. Aucun compte, schéma
métier, fonctionnalité produit, migration de données ou paramètre de
production n'est inclus. Ces stubs sont temporaires et réversibles.

## Prérequis

Installer Docker Desktop ou Docker Engine avec Docker Compose v2. Les services
locaux utilisent par défaut le port `5433` pour PostgreSQL, `8000` pour l'API
et `3010` pour l'interface sur `127.0.0.1`; vérifie qu'ils sont libres. Les
variables `DB_HOST_PORT`, `API_HOST_PORT` et `WEB_PORT` permettent de choisir
d'autres ports hôtes.

## Démarrer la base locale

```bash
docker compose up --build -d
docker compose ps --all
```

Compose attend le healthcheck `pg_isready` de PostgreSQL avant de lancer
Alembic, puis attend la réussite de la migration avant de démarrer l'API.
L'API passe healthy après une requête `SELECT 1` réussie; l'interface passe
healthy quand sa page répond. Le conteneur `migrate` s'arrête avec le code 0
lorsque la révision `0001_empty_baseline` a été appliquée. Pour vérifier la
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
uv run --project backend --locked --extra dev ruff check backend/app backend/migrations
uv run --project backend --locked python -m compileall -q backend/app backend/migrations
npm --prefix frontend run build
docker compose config --quiet
```

La CI exécute également le démarrage Compose, la migration ascendante et
descendante sur sa base jetable et les vérifications de santé. Ce scaffold ne
contient pas encore de suite de tests métier ni de scanner de dépendances dédié;
aucune de ces validations n'est présentée comme une preuve de fonctionnalités
Viewer ou Admin.

Réinitialiser la base locale en supprimant son volume et toutes ses données :

```bash
docker compose down --volumes
```

La variable optionnelle `POSTGRES_PASSWORD` remplace le mot de passe local de
démonstration. Ne réutilise jamais cette configuration ni ce mot de passe dans
un environnement partagé ou de production. Les migrations s'appliquent via
`alembic upgrade head`; leur retour arrière de développement est
`alembic downgrade base`, qui efface la ligne de version. Alembic conserve sa
table interne `alembic_version` vide. Il n'y a encore aucun schéma produit à
préserver.

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
contrôle sécurité, installe les dépendances verrouillées, lance le lint et le
build, puis joue le smoke test isolé. Il n'existe pas de déclencheur de push ni
de publication.

CI utilise uniquement le runner GitHub-hosted standard `ubuntu-latest`. Le
dépôt est public selon D-01; GitHub indique que ses runners standards sont
gratuits et sans limite de minutes pour les dépôts publics ([documentation
GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job)).
Aucun runner self-hosted, runner supérieur, secret ou service payant n'est
configuré ni requis.

Les documents canoniques commencent dans [docs/README.md](docs/README.md).

## Limites actuelles

Ce dépôt contient uniquement le scaffold technique et n'inclut pas encore les fonctionnalités produit ni une procédure de déploiement. Le cadrage n'autorise aucun accès ou changement à la production, aucune migration de données, aucune copie d'actif et aucune création de secret. La stratégie de données part d'une base V2 vide; les données de production V1 restent à inventorier avant toute décision de reprise. Les références visuelles, rendus navigateur, état d'exécution et publication effective des routes ou médias ne sont pas validés par l'inventaire statique.

Le cadrage de conception est `approved` depuis le 2026-11-16, après revue Produit, QA, audit indépendant et scan des marqueurs. Cette approbation autorise la planification des lots; elle ne certifie pas une application V2 ni l'exécution de tests ou contrôles visuels. Les lots doivent conserver leurs préconditions : comparaison de rendus et responsive/contrastes mesurés, tests V2, tests négatifs d’accès Admin côté serveur, preuve de droits avant copie de médias et décisions données/production/publication avant release.

## Suivi

Le suivi choisi est GitHub Projects, projet « Skkup V2 ». Le Project d'organisation a été créé et relu; sa vue par défaut montre `Todo`, `In Progress` et `Done`. Les issues MVP/Post-MVP #3 à #9 sont créées et relues. Les statuts actuels sont visibles dans le Project; P0 est mappé sur Priority `Urgent` et P1 sur `High`. Voir [l'état du suivi et les liens des issues](docs/project-management/github-project.md).
