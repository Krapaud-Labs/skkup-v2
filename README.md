# Skkup V2

Nouvelle base applicative publique pour la plateforme Skkup. Le dépôt contient actuellement le cadrage et les documents de conception; l'application n'est pas encore implémentée.

## Périmètre

Le projet vise à préserver les fonctions Viewer, Admin, publiques et d'extension présentes en V1, avec une refonte des dashboards et une nouvelle base technique. La vitrine et l'authentification doivent conserver leur rendu visible. Le détail des décisions, du barème et des vérifications restantes figure dans [la documentation](docs/README.md).

La couverture statique vérifiable de la référence V1 au commit `fcc4767f3ece9efc069d1a1c413942067cb89c93` comprend 27 pages applicatives, 81 routes HTTP et 58 entrées de médias runtime avec chemins, formats, dimensions et empreintes SHA-256 consignés. La méthode de comptage est reproductible depuis ce commit et l’inventaire média est détaillé dans [la readiness de conception](docs/design/design-readiness.md) et [le manifeste des médias](docs/design/media-inventory.md). Cette analyse statique ne valide ni le comportement réellement déployé, ni l’exécution des tests, ni la parité visuelle; les formes de réponse ou autorisations non établies restent signalées comme inconnues.

## Stack cible

- Interface : Next.js, React et TypeScript.
- API : FastAPI et Pydantic.
- Données : PostgreSQL, SQLAlchemy 2 et Alembic.
- Environnement : Docker Compose.
- CI visée : GitHub Actions.

Les versions exactes et les commandes d'installation/build seront fixées lors du premier scaffold. Aucun code produit n'est disponible pour exécuter l'application à ce stade.

## Prérequis et usage

Aucun outil applicatif n'est requis pour consulter le cadrage. Pour exécuter l'application, attendre les manifestes de dépendances et le guide de développement ajoutés avec le scaffold. Les documents canoniques commencent dans [docs/README.md](docs/README.md).

## Limites actuelles

Ce dépôt n'inclut pas encore l'application ni une procédure de déploiement. Le cadrage n'autorise aucun accès ou changement à la production, aucune migration de données, aucune copie d'actif et aucune création de secret. La stratégie de données part d'une base V2 vide; les données de production V1 restent à inventorier avant toute décision de reprise. Les références visuelles, rendus navigateur, état d'exécution et publication effective des routes ou médias ne sont pas validés par l'inventaire statique.

Le cadrage de conception est `approved` depuis le 2026-11-16, après revue Produit, QA, audit indépendant et scan des marqueurs. Cette approbation autorise la planification des lots; elle ne certifie pas une application V2 ni l'exécution de tests ou contrôles visuels. Les lots doivent conserver leurs préconditions : comparaison de rendus et responsive/contrastes mesurés, tests V2, tests négatifs d’accès Admin côté serveur, preuve de droits avant copie de médias et décisions données/production/publication avant release.

## Suivi

Le suivi choisi est GitHub Projects, projet « Skkup V2 ». Le Project d'organisation a été créé et relu; sa vue par défaut montre `Todo`, `In Progress` et `Done`. Les sept issues MVP/Post-MVP #3 à #9 sont créées et relues, toutes au statut `Todo`; P0 est mappé sur Priority `Urgent` et P1 sur `High`. Voir [l'état du suivi et les liens des issues](docs/project-management/github-project.md).
