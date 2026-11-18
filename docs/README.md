---
status: in-progress
last_updated: 2026-11-18
owner: Documentation
work_item: 2026-11-18-chain-issues-5-6-8-9
---

# Documentation de Skkup V2

Ce dossier décrit le périmètre, les parcours, la conception et les décisions de Skkup V2. Le cahier V1 archivé est une référence historique; le comportement doit être vérifié sur le commit source avant toute reprise d'actif ou gel d'un contrat.

| Document | Rôle | État |
| --- | --- | --- |
| [Vision et périmètre](product/vision-and-scope.md) | objectifs et frontières | cadré |
| [Stories](product/user-stories.md) | capacités et critères | US-02: 5/5 tests Auth et Ruff passent; #8 en revue; US-05 distingue tickets à gratter Classic/Premium et participations `raffleTicket`; D-16 fixe le gain Classic conditionné à un tirage ouvert, fallback points sinon |
| [Parcours](product/user-flows.md) | étapes et erreurs | cadré |
| [Architecture](design/architecture.md) | composants et flux | baseline à valider |
| [Direction visuelle](design/visual-direction.md) | direction Dashboard, densité, défilement et modales | exigences approuvées, rendu à vérifier par lot |
| [Données](design/data-model.md) | entités, règles et rétention | Auth/session #5 et progression #6 livrées dans `dev`; schéma Admin #8 présent sur branche, revue PostgreSQL et livraison en attente |
| [Contrats API](design/api-contracts.md) | HTTP et temps réel | Auth/session #5 et Viewer #6 livrés dans `dev`; contrats Admin #8 décrits sur la branche, QA navigateur et migration PostgreSQL en attente |
| [Menaces](security/threat-model.md) | menaces et contrôles | revue initiale |
| [Décisions](project-management/decision-log.md) | décisions et inconnues | D-16/D-20 distinguent les tickets à gratter `CLASSIC`/`PREMIUM` des participations `raffleTicket`; l’écart entre l’attribution V1 et V2 est décidé et à implémenter en #9 |
| [Suivi GitHub Projects](project-management/github-project.md) | choix et activation du suivi | pending_activation |
| [Roadmap](delivery/roadmap.md) | lots ordonnés | cadrage |
| [Readiness](design/design-readiness.md) | porte avant implémentation | cadrage approved; validations produit par lot, dont Auth #5, en attente |
| [Cahier archivé](project-management/cahier-des-charges/skkup-v2/) | source immuable | préservée |

## Limites

Ce cadrage ne crée pas l'application, ne copie aucun actif et n'autorise ni accès aux données de production, ni migration, ni déploiement. La baseline retient une base V2 vide; toute reprise de données exige un inventaire et une décision ultérieure. Les versions exactes et la matrice d'extension seront arrêtées au premier scaffold.

Le cahier accepté et son archive sont référencés dans le dépôt de documentation ci-dessus. Le profil technique sera matérialisé dans les manifestes publics au démarrage du scaffold.
