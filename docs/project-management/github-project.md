# Suivi GitHub Projects

## Décision et état vérifié

- Choix du propriétaire : GitHub Projects, projet « Skkup V2 ».
- Trello : désactivé.
- État distant : projet créé et relu le 2026-11-14; vue configurée. Le cadrage de conception a été approuvé le 2026-11-16 et les sept issues de planification/implémentation ont ensuite été créées et relues.
- Numéro : 5.
- URL : https://github.com/orgs/Krapaud-Labs/projects/5/views/1
- Visibilité observée : privée (icône de verrouillage). Le dépôt produit est public. La réponse « Public » du cadrage concernait le dépôt, pas une ouverture de visibilité du Project.
- Vérification visible le 2026-11-16 : Project #5 et ses colonnes ont été relus à l’URL ci-dessus; labels du dépôt consultés à https://github.com/Krapaud-Labs/skkup-v2/labels. Aucun changement de visibilité ou de colonnes n’a été effectué.

Le dépôt public `Krapaud-Labs/skkup-v2` existe. Le Project a été créé via la session GitHub dédiée et relu à l'URL ci-dessus. L'import automatique des issues a été désactivé. Le connecteur API ne propose pas la gestion Projects; l'interface a permis la création.

## Structure visée

La première vue est un Board, et son rendu final vérifié ne montre que les colonnes `Todo`, `In Progress` et `Done`. Les colonnes `Backlog` et `Ready` sont filtrées hors de la vue par défaut; elles ne contiennent aucun élément. Le champ Priority a été ajouté. La vue contient également Title, Assignees, Status, Linked pull requests et Sub-issues progress. Iteration, dates et dépendances restent à configurer si disponibles.

Le cadrage de conception a été approuvé le 2026-11-16. Les issues de planification/implémentation #3 à #9 sont créées et relues ci-dessous. L'ordre de travail suit d'abord l’infrastructure US-07, puis les lots MVP. Chaque issue conserve ses critères d’acceptation et les préconditions de son lot, notamment les contrôles de rendu/parité, les tests V2, les tests négatifs Admin côté serveur, les droits médias et les décisions de release qui s'y appliquent. Les issues sont planifiées; l'application V2 n'est pas encore implémentée.

## État réellement observé

Relecture distante le 2026-11-16 :

- Le dépôt `Krapaud-Labs/skkup-v2` reste public; le Project #5 « Skkup V2 » reste privé.
- La vue par défaut du Project n’affiche que `Todo`, `In Progress` et `Done`; les colonnes et la visibilité n’ont pas été modifiées.
- Les issues #3 à #9 existent, sont ouvertes sur GitHub et portent le statut Project `Todo`.
- Les sept issues portent le label actif `enhancement`.
- Les priorités des stories P0 sont enregistrées comme `Urgent` dans le champ Priority du Project; P1 est enregistré comme `High`.

## Issues de planification/implémentation créées et relues

Les critères ci-dessous proviennent des stories et des issues relues; les phases suivent `docs/delivery/roadmap.md`. Les gates design/sécurité et les règles métier sont reliés à `docs/design/design-readiness.md` et `docs/project-management/decision-log.md`. Les labels actifs du dépôt, consultés le 2026-11-16 à https://github.com/Krapaud-Labs/skkup-v2/labels, sont : `accessibility`, `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`. Les titres et corps encodent la phase MVP/Post-MVP; le champ **Priority** du Project porte `Urgent` pour P0 et `High` pour P1. Aucun label custom de phase ou de priorité n’est utilisé.

| Issue relue | Story(s) | Phase / lot | Priorité story → Project | Statut Project | Label | Critères d’acceptation sourcés | Gates préalables ou de livraison |
| --- | --- | --- | --- | --- | --- | --- |
| [#3](https://github.com/Krapaud-Labs/skkup-v2/issues/3) · [MVP] Préparer un environnement V2 isolé | US-07 | MVP / lot 3, préalable au lot 4 | P0 → Urgent | Todo / ouverte | `enhancement` | Docker démarre avec base vide, migrations et healthchecks; CI vérifie les artefacts. | Verrouiller les versions compatibles au scaffold conformément à D-13; vérifier migrations et healthchecks; garder les données de production hors de l’environnement; migration et publication requièrent une décision distincte. |
| [#4](https://github.com/Krapaud-Labs/skkup-v2/issues/4) · [MVP] Préserver la vitrine, les règles et les parcours publics V1 | US-01 | MVP / lot 4, après socle | P0 → Urgent | Todo / ouverte | `enhancement` | Sections, liens, langue, images utilisées et rendu correspondent à la V1 aux viewports du cahier. | Captures comparables V1/V2 et contrôle de parité avant fermeture du lot; vérifier responsive et contrastes; prouver les droits de chaque média avant copie. |
| [#5](https://github.com/Krapaud-Labs/skkup-v2/issues/5) · [MVP] Créer un compte et gérer la session membre | US-02 | MVP / lot 4, après socle | P0 → Urgent | Todo / ouverte | `enhancement` | Champs, validations, erreurs, consentement, rendu et permissions serveur conformes aux critères de la story. | Tests V2 API/UI et vérification des permissions serveur; contrôles de rendu et responsive; toute décision concernant données ou production reste un gate avant release. |
| [#6](https://github.com/Krapaud-Labs/skkup-v2/issues/6) · [MVP] Gérer les points et la progression Viewer | US-03 | MVP / lot 4, après socle | P0 → Urgent | Todo / ouverte | `enhancement` | Solde, ledger et progression cohérents; crédit quotidien idempotent; appliquer D-14 au ticket journalier, D-15 aux récompenses des paliers et D-16 aux tickets de grattage. | Écrire et exécuter des tests V2 d’idempotence, d’intégrité du ledger et des règles approuvées; n’introduire aucun plafond ou mécanisme non décidé. |
| [#7](https://github.com/Krapaud-Labs/skkup-v2/issues/7) · [MVP] Apparier l’extension et créditer l’activité éligible | US-04 | MVP / lot 4, après socle | P0 → Urgent | Todo / ouverte | `enhancement` | Appairage, révocation, crédits et plateformes conformes aux contrats confirmés. | Confirmer plateformes et package réellement pris en charge; tests V2 d’appairage/révocation/crédit; vérifier les droits des médias copiés et les exigences de release. |
| [#8](https://github.com/Krapaud-Labs/skkup-v2/issues/8) · [MVP] Gérer les objets autorisés dans l’administration | US-06 | MVP / lot 4, après socle | P0 → Urgent | Todo / ouverte | `enhancement` | Rôles vérifiés côté serveur, validations, créations modales et journalisation. | Établir la matrice rôle/action et les tests négatifs d’accès Admin côté serveur avant l’implémentation et la livraison des fonctions Admin; exécuter les tests V2 avant fermeture du lot. |
| [#9](https://github.com/Krapaud-Labs/skkup-v2/issues/9) · [Post-MVP] Implémenter les récompenses, tickets et tirages Viewer | US-05 | Post-MVP / lot 4, après socle et décision de lancement | P1 → High | Todo / ouverte | `enhancement` | Coût, résultat, historique et gagnants respectent les décisions et règles V1 arbitrées. | Tests V2 des coûts/résultats/historique/tirages; conserver D-07/D-08 et D-14 à D-16; toute décision de conformité, de production et d’activation publique doit être obtenue avant release. |

Lecture après création : les sept issues possèdent leurs critères, sources, priorités Project et label `enhancement`; leur état GitHub est ouvert et leur statut de board est Todo. Aucun statut Done n’est revendiqué.

## Checkpoint local

Le work item local actif reste la source d'avancement. Les issues #3 à #9 sont créées et relues; leur traitement suit l’ordre du lot 3, puis les lots MVP du lot 4, avec l’issue Post-MVP conservée à part. À chaque avancement, relire et synchroniser les statuts et preuves dans le Project et le profil du dépôt.
