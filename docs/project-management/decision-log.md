# Journal des décisions de cadrage

Date de mise à jour : 2026-11-18
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
| INIT-02 | Le suivi demandé est GitHub Projects, et non Trello. Le Project « Skkup V2 » (#5) a été créé et relu le 2026-11-14; sa vue par défaut a été vérifiée avec les colonnes Todo, In Progress et Done. La configuration éventuelle des itérations, dates et dépendances, ainsi que la couverture d’issues, restent à compléter après approbation de la readiness. | Décision explicite; Project créé et relu; champs et issues à compléter | Réponse propriétaire, item 2; `docs/project-management/github-project.md` | 2026-11-14 |
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
| D-14 | À la première connexion quotidienne, le ticket classique D-07 satisfait le palier de streak 1 du cahier et remplace les +5 points directs du check-in V1; n’ajouter aucun gain distinct ni cumul de ces deux récompenses. | Décision explicite | Réponse propriétaire, 2026-11-16, arbitrage 1; cahier §5.3 | 2026-11-16 |
| D-15 | Les tickets D-07 des paliers consécutifs 3/7/14/30 s’ajoutent aux cartes V1 conservées selon D-08. | Décision explicite | Réponse propriétaire, 2026-11-16, arbitrage 2 | 2026-11-16 |
| D-16 | Tout ticket attribué par une carte à gratter V1 est catégorisé comme ticket classique. | Décision explicite | Réponse propriétaire, 2026-11-16, arbitrage 3 | 2026-11-16 |
| D-17 | Utiliser un shell Dashboard unique partagé entre Viewer et Admin, avec des sections adaptées au rôle, une navigation cohérente et des permissions Admin vérifiées côté serveur. La décision n’approuve pas à elle seule la palette, les tokens, les layouts détaillés ni les états visuels. | Décision explicite | Réponse propriétaire, 2026-11-16, réponse « oui » à l’espace Dashboard unique avec sections par rôle | 2026-11-16 |
| D-18 | Valider la candidate visuelle V1 pour la palette et le langage de surface bleu nuit, les accents violet/cyan et un glow discret. Cette approbation ne fixe pas l’agencement, la densité, les breakpoints, les dimensions de panneaux ni les états détaillés, qui restent à valider techniquement. | Décision explicite, portée limitée à la palette et au langage visuel | Réponse propriétaire, 2026-11-16, « Valider la candidate V1 (Recommandé) » | 2026-11-16 |
| D-19 | Concevoir le Dashboard partagé dans le thème du site avec une présentation professionnelle, peu chargée et facile à parcourir. La page ne défile pas globalement; détails et éditions s’ouvrent dans des modales accessibles, dont le contenu peut défiler indépendamment si nécessaire. Cette décision ne modifie pas la parité V1 des pages Connexion/Inscription ni la modale d’acceptation du règlement. | Décision explicite | Réponse propriétaire, 2026-11-18, demande de prise en compte du Dashboard | 2026-11-18 |

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

## Articulation du barème acquis avec les règles V1

Lecture statique du commit de référence
`Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`, notamment
`backend/src/me/me.service.ts`,
`backend/src/watch-sessions/watch-sessions.service.ts` et
`backend/src/scratch-cards/scratch-cards.service.ts`. Les tests cités
ci-dessous existent dans l’arbre V1, mais aucun test n’a été exécuté pour
cette revue.

| Sujet | Valeur acquise du visuel (D-07) | Règle observée dans V1 | Articulation retenue | État |
| --- | --- | --- | --- | --- |
| Visionnage | Cumul horaire acquis : 10, 20, 35, 45, 55, 65, 75 et 90 points de 1 h à 8 h. | 10 points par heure pleine, +5 aux paliers de 3 h et 8 h; plafond V1 de 90 points de visionnage par jour. Les montants correspondent au visuel. | Conserver le barème et le plafond V1 de 90 points limités au visionnage. D-07 ne fixe aucun plafond global; aucune revalidation n’est requise. | Aucune pour le plafond: appliquer la baseline V1 au seul visionnage. |
| Première connexion / ticket classique | Tirage classique acquis : perdant 30 %, +5 points 15 %, +10 points 10 %, +15 points 5 %, ticket classique 40 %. | Le check-in quotidien V1 crédite directement 5 points; les paliers de streak débloquent des cartes à gratter. Le mécanisme observé ne montre pas le tirage probabiliste classique. | Appliquer D-14 : le ticket classique D-07 remplace les +5 points directs V1, et satisfait le palier de streak 1 du cahier sans autre gain distinct. | Arbitrée par D-14; test V2 à écrire avant implémentation. |
| Paliers de connexion | Récompenses additionnelles acquises après 3, 7, 14 et 30 jours de connexion consécutifs : respectivement +1 ticket classique, +2 classiques, +2 classiques et +1 premium, +2 classiques et +2 premium. | Le check-in V1 débloque une carte à gratter aux jours 3, 7, 14 et 30; il crée ensuite un ticket à chaque multiple de 10 strictement supérieur à 30. | Appliquer D-15 : les tickets D-07 s’ajoutent aux cartes V1 conservées selon D-08. | Arbitrée par D-15; l’extension de la série V1 au-delà du 30e jour reste à confirmer par le code exact. |
| Récompense des cartes à gratter | Le visuel ne définit ni probabilités ni gains de carte à gratter. | V1 : gains de points par palier (3: 10, 7: 15, 14: 25, 30: 40; défaut 10); le tirage prévoit 70 % points, 25 % rien, 5 % ticket, mais le ticket n’est attribué que si un tirage est ouvert. Sans tirage ouvert, ce résultat est remplacé par des points. Source : `backend/src/scratch-cards/scratch-cards.service.ts`; test existant `backend/test/scratch-card-no-win.e2e-spec.ts`. | Conserver cette règle V1 conditionnelle comme baseline V2 pour le sujet non spécifié par le visuel, conformément au choix recommandé accepté D-08; tout ticket V1 est classique selon D-16. | Arbitrée par D-16; tests V2 requis avant implémentation. |
| Ticket premium | Tirage premium acquis : +30 points 90 %, +40 points 5 %, +50 points 4 %, accès au concours 1 %; le visuel le rattache aux 14e et 30e jours consécutifs de connexion d’affilié. | Le check-in/carte consultés ne définissent pas cette catégorie de ticket premium ni cette table de résultats. | Appliquer la table premium D-07 aux paliers 14 et 30 consécutifs mentionnés, sans étendre son déclenchement à d’autres streaks; ces tickets s’ajoutent aux cartes selon D-15. | Arbitrée par D-15. |

Les valeurs D-07 retranscrites depuis le visuel sont acquises et ne sont pas
remises en question ici. Les règles V1 non couvertes par le visuel restent la
baseline recommandée acceptée par D-08. Les trois questions propriétaire
portant sur le check-in, le cumul des récompenses de streak et la catégorie du
ticket de grattage sont closes par D-14 à D-16. Les tests V1 n’ont pas été
lancés; leur présence ne prouve pas que les comportements sont déployés ou
encore souhaités.

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
2. L’extraction statique V1 des récompenses de cartes à gratter est consignée
   dans le tableau « Articulation du barème acquis avec les règles V1 », pour
   le commit `Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`.
   Les tests V1 n’ont pas été exécutés; le code ne prouve pas quel comportement
   est actuellement déployé. Les scénarios et tests V2 restent à spécifier et
   à écrire avant l’implémentation.
3. Navigateurs/OS réellement pris en charge et testés par l’extension.
4. Contrat Socket.IO, noms et charges utiles des événements ainsi que les
   besoins de jobs/pub-sub, à extraire avant le gel technique.
5. Service d’email et conditions d’envoi pour parrainage et récupération de
   compte.
6. Versions exactes de Python, Node.js, PostgreSQL, Next.js, FastAPI et outils
   de test, à vérifier au premier scaffold avant verrouillage.
7. Aucune inconnue observée concernant l’existence, le numéro (#5) ou l’URL du
   GitHub Project, consignés dans `docs/project-management/github-project.md`
   et relus le 2026-11-14. Les configurations d’itération, de dates et de
   dépendances restent à vérifier selon les capacités disponibles; la
   couverture d’issues est reportée jusqu’à l’approbation de la readiness.

## Historique et limites

Le cahier actif fourni porte encore son statut source `reconstructed`; ce
journal consigne la validation ultérieure du propriétaire et ses réponses
datées du 2026-11-14. L’archive initiale du cahier doit rester inchangée. Les
inconnues listées sont des vérifications ou décisions localisées par sujet;
elles ne révoquent pas les décisions déjà prises et ne valent pas autorisation
de modifier le produit ou la production.
