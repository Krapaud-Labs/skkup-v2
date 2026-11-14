# Roadmap de cadrage et livraison

| Lot | Objectif | Dépendances | Sortie | État |
| --- | --- | --- | --- | --- |
| 0. Cadrage | valider périmètre, décisions et barème | réponses propriétaire | cahier actif, décisions, profil | en livraison |
| 1. Inventaire V1 | relier routes, règles, clients, tests et actifs | accès au commit source | matrice de parité et inconnues confirmées | à planifier |
| 2. Architecture détaillée | figer API, modèle, sécurité, plateforme après vérifications | lot 1 | design readiness approuvée | en draft |
| 3. Socle | scaffold web/API/base, conteneurs, CI et commandes | lot 2, versions compatibles | build reproductible et migrations vides | futur |
| 4. Parité par parcours | livrer fonctions par domaine avec tests et accessibilité | socle, stories confirmées | lots intégrés via PR vers dev | futur |
| 5. Mise en production | décider migration, juridique, hébergement et déploiement | validation propriétaire et audits | plan/rollback approuvés puis promotion séparée | hors de ce Goal |

## Validation, déploiement et retour arrière

Les lots de code définiront leurs contrôles ciblés, puis une passe QA/sécurité/accessibilité proportionnée avant livraison. Le déploiement n'est pas autorisé par ce cadrage. Avant toute migration future, exiger sauvegarde vérifiée, environnement isolé, plan de retour arrière et décision explicite. Les données V1 ne sont ni consultées ni modifiées ici.

## Report et dette

Versions exactes, hébergeur, email, Redis/worker, métriques et détails d'API temps réel sont différés jusqu'aux preuves V1 ou au scaffold correspondant. Ce report évite de transformer des hypothèses en contrats irréversibles.
