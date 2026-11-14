# User stories et critères d'acceptation

Les stories sont des exigences de cadrage. Routes, contrôles et états exacts doivent être relevés dans les sources et tests V1 avant toute déclaration de parité.

| ID | Prio | Story | Critères vérifiables | Preuve prévue | Statut |
| --- | --- | --- | --- | --- | --- |
| US-01 | P0 | Comme visiteur, je découvre le service et ses règles. | Sections, liens, langue, images utilisées et rendu correspondent à la V1 aux viewports du cahier. | inventaire, captures, image-diff | à inventorier |
| US-02 | P0 | Comme membre, je crée un compte et gère ma session. | Champs, validations, erreurs, consentement, rendu fidèles; permissions côté serveur. | tests API/UI, comparaison V1 | à inventorier |
| US-03 | P0 | Comme Viewer, je consulte points et progression. | Solde, ledger et progression cohérents; crédit quotidien idempotent. | tests métier/intégrité | règles V1 à extraire |
| US-04 | P0 | Comme Viewer, j'apparie l'extension et suis une activité éligible. | Appairage, révocation, crédits et plateformes conformes aux contrats confirmés. | tests d'intégration isolés | à inventorier |
| US-05 | P1 | Comme Viewer, j'utilise récompenses, tickets et tirages disponibles. | Coût, résultat, historique et gagnants respectent les décisions et règles V1 arbitrées. | cas métier, journal d'audit | à arbitrer |
| US-06 | P0 | Comme Admin, je gère les objets autorisés. | Rôles vérifiés côté serveur, validations, créations modales et journalisation. | tests de permission/parcours | à inventorier |
| US-07 | P0 | Comme exploitant, je prépare un environnement V2 isolé. | Docker démarre avec base vide, migrations et healthchecks; CI vérifie les artefacts. | procédure et CI | après cadrage |

## Cas négatifs

Crédit dupliqué, solde incohérent, session expirée/révoquée, rôle insuffisant, appairage invalide ou réutilisé, plateforme non éligible, achat concurrent, règle contradictoire et service externe indisponible.

Sécurité, confidentialité, accessibilité, fidélité visuelle, intégrité transactionnelle et observabilité doivent recevoir des seuils mesurables avant les cartes d'implémentation. Les budgets de performance et disponibilité sont à définir après mesure.
