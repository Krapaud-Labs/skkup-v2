# Roadmap de cadrage et livraison

| Lot | Objectif | Dépendances | Sortie | État |
| --- | --- | --- | --- | --- |
| 0. Cadrage | valider périmètre, décisions et barème | réponses propriétaire | cahier actif, décisions, profil | complété |
| 1. Inventaire V1 | relier statiquement routes, règles, clients, tests et médias | accès au commit source | 27 pages, 81 routes HTTP, 58 entrées média métadonnées, méthode reproductible et limites/inconnues documentées | complété statique; parité visuelle et comportement runtime restent non vérifiés |
| 2. Architecture détaillée | figer API, modèle, sécurité, plateforme après vérifications | lot 1 | design readiness approuvée au niveau cadrage | cadrage approuvé; contrats détaillés et préconditions par lot à suivre |
| 3. Socle | scaffold web/API/base, conteneurs, CI et commandes | lot 2, versions compatibles | build reproductible et migrations vides | complété, issue #3 fusionnée dans dev via PR #11; les lots produit 4 restent à livrer |
| 4. Parité par parcours | livrer fonctions par domaine avec tests et accessibilité | socle, stories confirmées | lots intégrés via PR vers dev | Chaîne autorisée en dev le 2026-11-18. #5 Auth/session livré via PR #14; #6 points/progression et Dashboard Viewer via PR #15; #8 Admin via PR #16; kit shared 2.0.12 aligné via PR #17. #9, tickets à gratter `CLASSIC`/`PREMIUM` distincts des participations aux tirages, livré via PR #18 fusionnée dans `dev` au commit `05b12fcd30b6d0191e060afda6749bc5b0ea2b04`; CI run `44405572786` réussie. D-21 confirme qu’un résultat PREMIUM « Accès au concours » à 1 % attribue une participation distincte; le correctif est en cours sur `feat/issue-9-premium-entry`, avec refus pré-RNG conservé sans tirage ouvert éligible. Aucune activation publique ni promotion `main`. |
| 5. Mise en production | décider migration, juridique, hébergement et déploiement | validation propriétaire et audits | plan/rollback approuvés puis promotion séparée | hors de ce Goal |

## Validation, déploiement et retour arrière

Les lots de code définiront leurs contrôles ciblés, puis une passe QA/sécurité/accessibilité proportionnée avant livraison. Le déploiement n'est pas autorisé par ce cadrage. Avant toute migration future, exiger sauvegarde vérifiée, environnement isolé, plan de retour arrière et décision explicite. Les données V1 ne sont ni consultées ni modifiées ici.

## Report et dette

Versions exactes, hébergeur, email, Redis/worker, métriques et détails d'API temps réel sont différés jusqu'aux preuves V1 ou au scaffold correspondant. Ce report évite de transformer des hypothèses en contrats irréversibles.
