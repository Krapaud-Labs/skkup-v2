# Journal des décisions de cadrage

Date de mise à jour : 2026-11-14
Projet : Skkup V2
Référence produit : dépôt `Krapaud-Labs/Skkup`, branche `dev`, commit
`fcc4767f3ece9efc069d1a1c413942067cb89c93`, selon le cahier provisoire.

Ce journal consigne séparément les faits rapportés par les sources, les choix
explicitement faits par le propriétaire, les interprétations réversibles et les
inconnues qui nécessitent une vérification. Il ne remplace pas le cahier
d’origine ni son archive.

## Sources

| Référence | Nature | Date |
| --- | --- | --- |
| Cahier de cadrage reçu, version 2.0-draft | Périmètre, contraintes, règles proposées et questions D-01 à D-13 | 2026-11-14 |
| Réponses du propriétaire dans la conversation, items 1 à 15 | Validation du cahier comme base et choix listés ci-dessous | 2026-11-14 |
| `Systeme_de_points_.png` fourni par le propriétaire | Barème demandé comme source pour D-07 | 2026-11-14 |

## Décisions prises

| ID | Décision | Type et état | Source | Date |
| --- | --- | --- | --- | --- |
| INIT-01 | Le cahier provisoire est validé comme base du cadrage V2. Cette validation autorise la formalisation et la conception; elle n’autorise pas à elle seule une bascule de production ou une modification de données de production. | Décision explicite | Réponse propriétaire, item 1 | 2026-11-14 |
| INIT-02 | Le suivi demandé est GitHub Projects, et non Trello. Le Project s’appelle « Skkup V2 ». Le suivi distant reste en attente tant que le Project et sa relecture ne sont pas prouvés. | Décision explicite; synchronisation à vérifier | Réponse propriétaire, item 2; profil projet | 2026-11-14 |
| D-01 | Le dépôt cible recommandé `Krapaud-Labs/skkup-v2` est public. | Décision explicite sur la visibilité; nom tiré de la proposition du cahier | Réponse propriétaire, item 3; §11 du cahier | 2026-11-14 |
| D-02 | Utiliser Next.js avec React et TypeScript. Garder la vitrine et les pages Connexion/Inscription visuellement identiques à la référence selon les critères du cahier. | Décision explicite | Réponse propriétaire, item 4; §4 et §6 du cahier | 2026-11-14 |
| D-03 | Préserver d’abord les chemins et payloads API consommés par l’extension publiée. Toute évolution de contrat doit être versionnée. | Recommandation acceptée | Réponse propriétaire, item 5; §11 du cahier | 2026-11-14 |
| D-04 | Préserver la compatibilité avec le client temps réel existant; garder REST comme voie de récupération. Une migration coordonnée reste possible si l’extraction montre que la compatibilité ne peut être conservée. | Recommandation acceptée, interprétation de mise en œuvre conservatrice | Réponse propriétaire, item 6; §11 du cahier | 2026-11-14 |
| D-05 | Ajouter Redis et un worker Python seulement si les besoins effectifs de tâches ou de pub/sub le démontrent. Le choix Celery ou alternative est différé à cette vérification. | Recommandation acceptée | Réponse propriétaire, item 7; §11 du cahier | 2026-11-14 |
| D-06 | La base V2 démarre vide. Avant toute migration ou bascule, inventorier l’ancienne production et faire confirmer les éléments à conserver. Aucun contenu, compte ou historique n’est réputé migré par défaut. | Recommandation acceptée; inventaire de production inconnu | Réponse propriétaire, item 8; §8 et §11 du cahier | 2026-11-14 |
| D-07 | Utiliser le barème du visuel fourni pour les règles qu’il couvre. Les valeurs de visionnage sont cumulées jusqu’à 90 points à 8 h; 65 points correspondent au seuil de 6 h. Le visuel ne fixe pas à lui seul un plafond global réunissant les sources de points. | Décision explicite par fourniture du barème; portée limitée à ce qu’il montre | Réponse propriétaire, item 9; `Systeme_de_points_.png` | 2026-11-14 |
| D-08 | Prendre comme référence les règles de récompenses réellement actives dans le code et les tests V1. Les montants ou probabilités qui n’y sont pas documentés doivent rester explicitement inconnus jusqu’à arbitrage. | Recommandation acceptée; extraction V1 à faire | Réponse propriétaire, item 10; §11 du cahier | 2026-11-14 |
| D-09 | Limiter les plateformes de l’extension à celles réellement actives et testées dans la référence V1. | Recommandation acceptée; matrice exacte à extraire | Réponse propriétaire, item 11; §11 du cahier | 2026-11-14 |
| D-10 | Conserver la boutique de tickets en développement. Ne pas revendiquer sa conformité ni l’activer publiquement avant un réexamen des règles applicables. | Recommandation acceptée; décision d’activation publique différée | Réponse propriétaire, item 12; §11 du cahier | 2026-11-14 |
| D-11 | Initialiser le premier compte Admin par une procédure hors interface, ponctuelle, auditée et désactivée après usage; aucun endpoint d’auto-promotion. | Recommandation acceptée | Réponse propriétaire, item 13; §11 du cahier | 2026-11-14 |
| D-12 | Garder les codes consultables dans « Mes achats ». Ne promettre aucun email tant qu’un service n’est pas choisi et configuré. | Recommandation acceptée; service d’email inconnu | Réponse propriétaire, item 14; §11 du cahier | 2026-11-14 |
| D-13 | Partir de la baseline du §6.2 du cahier, puis vérifier et verrouiller les versions compatibles au premier démarrage technique. | Recommandation acceptée; versions exactes différées | Réponse propriétaire, item 15; §6.2 et §11 du cahier | 2026-11-14 |

## Barème approuvé issu de l’image

### Ticket journalier classique

| Résultat | Probabilité |
| --- | ---: |
| Perdant | 30 % |
| +5 points | 15 % |
| +10 points | 10 % |
| +15 points | 5 % |
| 1 ticket classique | 40 % |

Total : 100 %.

### Ticket premium

L’image associe le ticket premium au 14e et au 30e jour consécutif de
connexion.

| Résultat | Probabilité |
| --- | ---: |
| +30 points | 90 % |
| +40 points | 5 % |
| +50 points | 4 % |
| Accès au concours | 1 % |

Total : 100 %.

### Récompenses de connexion consécutive

| Palier | Récompense additionnelle | Total avec les tickets journaliers |
| --- | --- | --- |
| 3 jours | +1 ticket classique | 2 tickets classiques |
| 7 jours | +2 tickets classiques | 3 tickets classiques |
| 14 jours | +2 classiques et +1 premium | 3 classiques et 1 premium |
| 30 jours | +2 classiques et +2 premium | 3 classiques et 2 premium |

### Visionnage et autres valeurs

| Temps de visionnage cumulé | Points cumulés |
| --- | ---: |
| 1 h | 10 |
| 2 h | 20 |
| 3 h | 35 |
| 4 h | 45 |
| 5 h | 55 |
| 6 h | 65 |
| 7 h | 75 |
| 8 h | 90 |

- Prix du ticket d’accès au concours : 2 500 points.
- Parrainage : 15 points pour le parrain et 15 pour le nouvel inscrit qui
  s’inscrit via le lien de parrainage reçu par email.

## Hypothèses réversibles

- Pour D-04, la compatibilité existante est la voie de départ, car elle évite
  une rupture de l’extension. Le protocole et les événements exacts restent à
  vérifier dans la référence avant de figer le contrat V2.
- Pour D-06, « base vide » signifie que la V2 ne sera pas initialisée depuis
  les données V1. Cela ne signifie pas que les données V1 sont inexistantes ou
  qu’elles peuvent être supprimées.
- Pour D-07, « 90 points à 8 h » décrit le barème de visionnage de l’image. Cela
  ne prouve pas un plafond total journalier incluant les points de connexion,
  parrainage, cartes ou récompenses.
- Le lien de parrainage décrit comme reçu par email dépend de la décision D-12:
  aucun envoi effectif n’est promis avant le choix et la configuration d’un
  service d’email.

## Inconnues à vérifier avant les lots concernés

1. Données réellement présentes dans l’ancienne production et décision
   spécifique sur tout contenu ou historique à préserver. Aucun accès à cette
   base n’est inclus dans le cadrage.
2. Récompenses de cartes à gratter et règles non couvertes par l’image, à
   extraire du code et des tests de la référence.
3. Navigateurs/OS réellement pris en charge et testés par l’extension.
4. Contrat Socket.IO, noms et charges utiles des événements ainsi que les
   besoins de jobs/pub-sub, à extraire avant le gel technique.
5. Service d’email et conditions d’envoi pour parrainage et récupération de
   compte.
6. Versions exactes de Python, Node.js, PostgreSQL, Next.js, FastAPI et outils
   de test, à vérifier au premier scaffold avant verrouillage.
7. Création effective du GitHub Project, ses champs, vues et Issues. Le choix
   est confirmé, mais aucun identifiant ou URL distant n’est consigné dans le
   profil actuel.

## Historique et limites

Le cahier actif fourni porte encore son statut source `reconstructed`; ce
journal consigne la validation ultérieure du propriétaire et ses réponses
datées du 2026-11-14. L’archive initiale du cahier doit rester inchangée. Les
inconnues listées sont des vérifications ou décisions localisées par sujet;
elles ne révoquent pas les décisions déjà prises et ne valent pas autorisation
de modifier le produit ou la production.
