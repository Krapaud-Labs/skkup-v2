# Skkup V2

Nouvelle base applicative publique pour la plateforme Skkup. Le dépôt contient actuellement le cadrage et les documents de conception; l'application n'est pas encore implémentée.

## Périmètre

Le projet vise à préserver les fonctions Viewer, Admin, publiques et d'extension présentes en V1, avec une refonte des dashboards et une nouvelle base technique. La vitrine et l'authentification doivent conserver leur rendu visible. Le détail des décisions, du barème et des vérifications restantes figure dans [la documentation](docs/README.md).

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

Ce dépôt n'inclut pas encore l'application ni une procédure de déploiement. Le cadrage n'autorise aucun accès ou changement à la production, aucune migration de données, aucune copie d'actif et aucune création de secret. La stratégie de données part d'une base V2 vide; les données V1 restent à inventorier avant toute décision de reprise.

## Suivi

Le suivi choisi est GitHub Projects, projet « Skkup V2 ». Son activation distante reste en attente de création et de relecture vérifiable. Voir [l'état du suivi](docs/project-management/github-project.md).
