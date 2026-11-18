# Documentation de Skkup V2

Ce dossier décrit le périmètre, les parcours, la conception et les décisions de Skkup V2. Le cahier V1 archivé est une référence historique; le comportement doit être vérifié sur le commit source avant toute reprise d'actif ou gel d'un contrat.

| Document | Rôle | État |
| --- | --- | --- |
| [Vision et périmètre](product/vision-and-scope.md) | objectifs et frontières | cadré |
| [Stories](product/user-stories.md) | capacités et critères | US-02: 5/5 tests Auth et Ruff passent; comparaison visuelle Auth effectuée avec écarts estimatifs; parité complète et PostgreSQL/Docker à vérifier |
| [Parcours](product/user-flows.md) | étapes et erreurs | cadré |
| [Architecture](design/architecture.md) | composants et flux | baseline à valider |
| [Direction visuelle](design/visual-direction.md) | direction Dashboard, densité, défilement et modales | exigences approuvées, rendu à vérifier par lot |
| [Données](design/data-model.md) | entités, règles et rétention | conceptuel; tables Auth/session #5 présentes, non validées |
| [Contrats API](design/api-contracts.md) | HTTP et temps réel | Auth/session #5: 5/5 tests Auth et Ruff passent; comparaison visuelle effectuée sans mesure quantitative; parité complète et migration PostgreSQL en attente; autres contrats à confronter à V1 |
| [Menaces](security/threat-model.md) | menaces et contrôles | revue initiale |
| [Décisions](project-management/decision-log.md) | décisions et inconnues | vivant |
| [Suivi GitHub Projects](project-management/github-project.md) | choix et activation du suivi | pending_activation |
| [Roadmap](delivery/roadmap.md) | lots ordonnés | cadrage |
| [Readiness](design/design-readiness.md) | porte avant implémentation | cadrage approved; validations produit par lot, dont Auth #5, en attente |
| [Cahier archivé](project-management/cahier-des-charges/skkup-v2/) | source immuable | préservée |

## Limites

Ce cadrage ne crée pas l'application, ne copie aucun actif et n'autorise ni accès aux données de production, ni migration, ni déploiement. La baseline retient une base V2 vide; toute reprise de données exige un inventaire et une décision ultérieure. Les versions exactes et la matrice d'extension seront arrêtées au premier scaffold.

Le cahier accepté et son archive sont référencés dans le dépôt de documentation ci-dessus. Le profil technique sera matérialisé dans les manifestes publics au démarrage du scaffold.
