# Vision, objectifs et périmètre

## Contexte

Skkup V2 renouvelle la base technique et les dashboards de la plateforme de points et récompenses, en préservant les parcours publics, l'extension et les fonctions Viewer/Admin réellement présentes en V1. Le cahier reconstruit décrit l'intention; un inventaire de parité sur le commit `fcc4767f3ece9efc069d1a1c413942067cb89c93` reste requis avant développement.

## Acteurs

| Acteur | Besoin | Résultat |
| --- | --- | --- |
| Visiteur | comprendre service et règles | pages publiques fidèles à la V1 |
| Viewer | gérer compte, activité et récompenses | règles explicites et parcours équivalents |
| Admin | gérer contenus, utilisateurs et opérations permises | droits vérifiés côté serveur et traçabilité |
| Exploitant | opérer la plateforme | procédures sûres, sans changement prod durant le cadrage |

## Objectifs

- Documenter les capacités V1 à préserver et leurs critères de parité.
- Refaire les dashboards avec React/TypeScript sans changer le rendu de la vitrine et de l'authentification.
- Cibler FastAPI, PostgreSQL, SQLAlchemy 2 et Alembic avec contrats contrôlés.
- Prévoir une base V2 vide; statuer séparément sur les données existantes.

Les cibles chiffrées d'usage, disponibilité et performance restent à mesurer.

## Périmètre

Vitrine et pages de connexion/inscription à fidélité visuelle stricte; dashboards Viewer/Admin reconstruits; points, extension, récompenses, tickets, tirages, contenu, administration et temps réel selon parité vérifiée; API, base, migrations, conteneurs et CI de développement.

## Hors périmètre du cadrage

Code produit, copie d'actifs, accès à la base de production, migration, suppression de données, secrets, hébergeur et déploiement. Toute différence visuelle exige une décision explicite.

## Hypothèses et validations

- Le dépôt public `Krapaud-Labs/skkup-v2` existe et constitue la cible.
- La V1 est référence fonctionnelle; chaque capacité et règle contradictoire doit être reliée au code/tests.
- Les barèmes joints sont transcrits dans `project-management/decision-log.md`; l'implémentation attend l'extraction des règles effectives V1.
- Plateformes d'extension, volumes, performance et hébergement restent à vérifier.
