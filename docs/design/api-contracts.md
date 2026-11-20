---
status: in-progress
last_updated: 2026-11-18
owner: Documentation
work_item: 2026-11-18-chain-issues-5-6-8-9
---

# Contrats d'interfaces

## Décisions et limites

API cible REST JSON/OpenAPI avec FastAPI/Pydantic. La compatibilité Socket.IO du client existant est à préserver jusqu'à l'inventaire des contrats et clients publiés. Le tableau présente les frontières de conception; les sections ultérieures distinguent les contrats V2 effectivement implémentés.

| Domaine | Consommateur | Responsabilité | Autorisation à spécifier | Preuve avant implémentation |
| --- | --- | --- | --- | --- |
| Authentification/session | site | ouvrir, terminer, consulter une session, changer le mot de passe | compte concerné, anti-abus, origine autorisée | 5 tests Auth et Ruff passent; comparaison visuelle V1/V2 effectuée sur captures, parité fonctionnelle complète et PostgreSQL/Docker en attente |
| Profil/activité | site | profil, solde, ledger, progression, inventaire des tickets | propriétaire du compte | #6: routes Viewer fusionnées dans `dev` via PR #15 |
| Appairage/visionnage | extension | lier appareil, envoyer activité admissible | jeton révocable | routes, payloads, plateformes |
| Récompenses/tirages | site | gratter, acheter une participation, tirer, historiser | rôle Viewer/Admin et états métier | #9 implémenté sur la branche feature; QA et audit final avant livraison `dev` |
| Administration | dashboard Admin | gérer utilisateurs et contenus | rôle/ressource côté serveur | matrice d'accès et journal |
| Temps réel | site/extension | notifier changements | handshake, rooms isolées | protocole Socket.IO V1 |

## Conventions à décider au scaffold

Versionnement, erreurs, pagination, idempotence, tailles maximales, délais et retry seront spécifiés en cohérence avec les clients V1. Les réponses n'exposent pas l'existence d'un compte. L'API est la source de vérité des droits, soldes, durées créditées et états de tirage.

## Compatibilité

Ne pas changer les routes ou payloads consommés par l'extension sans versionnement et migration coordonnée. REST permet de récupérer l'état si le temps réel échoue. Les exemples concrets attendent la comparaison au commit V1.

## Points et progression Viewer, lot #6 livré dans `dev`

Toutes les routes de cette section exigent une session web authentifiée. Les
résultats sont rattachés à l'identité de session; le client ne fournit pas le
`user_id` cible. Ces routes ont été livrées dans `dev` via la PR #15, merge
commit `eb3b129`.

| Méthode et route | Contrat implémenté |
| --- | --- |
| `GET /me` | Profil: `id`, `email`, `pseudo`, `role`, `soldePoints`, `streakActuel`, `streakMax`, `derniereVisiteAt`, `createdAt`. |
| `GET /me/points` | Résumé: `soldePoints`, `streakActuel`, `streakMax`, `derniereVisiteAt`, `prochainPalierStreak`, `ticketsDisponibles` de tickets à gratter `CLASSIC`/`PREMIUM`. Compare le solde utilisateur à la somme du registre et renvoie HTTP 500 en cas de divergence. |
| `GET /me/points/history?page=1&limit=20` | Historique paginé, `limit` borné à 1–100; retourne `transactions` (`id`, `userId`, `type`, `montant`, `watchSessionId`, `shopPurchaseId`, `createdAt`), `page`, `limit`, `total`, `totalPages`. |
| `GET /me/reward-tickets?page=1&limit=20` | Inventaire paginé des tickets à gratter `CLASSIC`/`PREMIUM` non consommés, limite 1–100; chaque ticket expose `id`, `categorie`, `origine`, `obtenuLe`, avec `page`, `limit`, `total`, `totalPages`. Cette route n'effectue ni grattage ni inscription à un tirage. |
| `POST /me/daily-checkin` | Sans payload métier; vérifie l'origine et la session. Enregistre au plus un check-in par journée métier et réexpose le même résultat lors d'un replay. Attribue le ticket à gratter quotidien `CLASSIC`; applique les tickets à gratter additionnels de palier D-15 et crée les grants de cartes V1 aux paliers prévus. Réponse: `id`, `jourConnexion`, `streakActuel`, `streakMax`, `soldePoints`, `pointsCredites` (0), `ticketsAttribues[]`, `carteAGratterDebloquee`, `palierCarte` et `carteDebloquee` (ou `null`). |

Le jour métier utilise `TZ` avec `Europe/Paris` par défaut. D-14 à D-16
régissent les attributions; D-20 précise que les catégories `CLASSIC` et
`PREMIUM` sont des tickets à gratter, distincts des participations au tirage.
Le code V1 créait une entrée `raffleTicket` pour le gain « ticket » si un tirage
était ouvert. Selon D-16/D-20, V2 attribue à la place un ticket à gratter
`CLASSIC` sous cette condition et conserve le fallback points V1 en l’absence
de tirage ouvert. `reward_tickets` reste un inventaire de tickets à gratter,
jamais une entrée de tirage; la participation est portée séparément par
`raffleTicket`. « Accès au concours » reste un résultat distinct. Les tests
ciblés rapportés par QA couvrent l'isolation Viewer, le
replay quotidien, le rollback, le ledger et ces décisions; Ruff passe et la
migration DDL a été exercée sous SQLite. Ni migration PostgreSQL, ni test de
concurrence mult-processus sur PostgreSQL ne sont revendiqués. Le grant de
carte ne contient pas encore le résultat ou le mécanisme de grattage; le
grattage des tickets `CLASSIC`/`PREMIUM` et l’attribution des participations
au tirage, qui en sont distinctes, restent au lot #9.

## Authentification/session, lot #5 livré dans `dev`

Le backend V2 contient actuellement les routes suivantes, sous réserve de
validation indépendante et de vérification d'intégration :

| Méthode et route | Fonction | Contrat actuellement implémenté |
| --- | --- | --- |
| `POST /auth/register` | inscription | `email`, `pseudo`, `motDePasse`, `accepteReglement`; `201`, `{ "pseudo" }`, cookie de session |
| `POST /auth/login` | connexion | `email`, `motDePasse`; `200`, `{ "pseudo" }`, cookie de session |
| `GET /auth/session` | session courante | profil public si authentifié, sinon `{ "authentifie": false, "profil": null }` |
| `POST /auth/logout` | déconnexion | `204`, révocation de la session valide et suppression du cookie |
| `PATCH /auth/password` | changement de mot de passe | `ancienMotDePasse`, `nouveauMotDePasse`; `204`, révocation des sessions web |

Les jetons signés HS256 ont une durée de 24 heures. L'API vérifie le jeton
contre une ligne `auth_sessions` persistée et le compte actif. L'inscription
crée un compte Viewer et exige l'acceptation explicite du règlement. Le
changement de mot de passe incrémente `session_version`, révoque toutes les
sessions web V2 et efface le cookie courant. Cette version est l'epoch de
révocation commun à porter et vérifier côté serveur pour de futurs credentials.

Ce lot ne comprend pas les domaines d'appairage et de visionnage. Les tables,
routes et mécanismes V2 correspondants ne sont pas présents dans le périmètre
Auth décrit ici. En conséquence, l'invalidation des appairages, tokens
d'appairage et sessions de visionnage V1 n'est pas effective en V2 à ce stade;
la parité correspondante dépend du lot #7. Aucun comportement de ces domaines
ne doit être inféré de `session_version` seul.

Le contrat ci-dessus est une description de l'état du code, pas une preuve de
parité fonctionnelle complète. QA rapporte cinq tests Auth réussis : quatre
tests de contrat ASGI direct avec SQLite en mémoire et un test unitaire du
rollover au changement de jour civil. Les contrats couvrent validation,
consentement, cookie, profil Viewer, erreurs de connexion, révocation à la
déconnexion et au changement de mot de passe, origine autorisée et préflight
CORS. Ruff sur `backend/app`, `backend/migrations` et `backend/tests` passe
également. Les tests ne couvrent pas une base PostgreSQL ni l'intégration
complète dans un navigateur. QA a aussi comparé des captures Chromium headless
locales V1/V2 desktop, mobile et inscription. Les écarts visuels restants ont
été estimés à environ 10–20 px sur mobile et 5 px sur la modale selon les vues;
aucune mesure différentielle quantitative n'est disponible, donc le pixel-perfect
n'est pas revendiqué. Sur la modale mobile, le document mesurait
999 px pour un viewport de 844 px; le CTA à y=902 est devenu visible après
`scrollY=155`. Vingt pressions Tab sont restées dans la modale sans soumettre
le formulaire. Ces observations ciblées ne prouvent pas une couverture
complète des formulaires, de la navigation ou de l'accessibilité clavier. La
parité fonctionnelle complète reste ouverte. La migration PostgreSQL via
Docker n'a pas été vérifiée, le socket Docker ayant été refusé dans
l'environnement QA.

## Administration V2, issue #8 en revue sur sa branche

Chaque route `/admin/*` requiert une session web valide et un rôle Admin relu
côté serveur. Les mutations exigent une origine autorisée; les écritures
sensibles et transitions sont auditées transactionnellement. Les détails
complets des champs, validations et réponses figurent dans
[`backend/README.md`](../../backend/README.md).

| Méthode et route | Contrat implémenté sur la branche #8 |
| --- | --- |
| `GET /admin/users`, `GET /admin/users/{id}`, `GET /admin/users/{id}/audit` | Liste bornée, fiche et événements de statut; recherche sur pseudo/email. |
| `PATCH /admin/users/{id}/status` | Active/désactive un compte, révoque ses sessions web lors de la désactivation; aucune modification de rôle ou auto-désactivation. |
| `GET/POST /admin/announcements`, `PATCH /admin/announcements/{id}`, `POST /admin/announcements/{id}/publish`, `DELETE /admin/announcements/{id}`, `POST /admin/announcements/{id}/restore/{eventId}`, `GET /admin/announcements/{id}/history` | Cycle de vie et restauration par événements d'audit; mutations limitées par origine autorisée. |
| `GET/POST /admin/content`, `GET/PATCH /admin/content/{id}`, `POST /admin/content/{id}/publish`, `GET /admin/content/{id}/history`, `POST /admin/content/{id}/restore/{version}` | Contenu typé/localisé, versionnement des changements; le JSON imbriqué reste opaque. |
| `GET/POST /admin/sponsors`, `PATCH /admin/sponsors/{id}` | Catalogue source V1; URLs de logo HTTPS; pas de suppression dédiée; `_count.lots` reste `null`. |
| `GET /admin/dashboard/summary` | Indicateurs présents et bornés; données non implémentées explicitement marquées comme indisponibles. |
| `GET /admin/audit?page=1&limit=20` | Chronologie paginée; données personnelles et métadonnées brutes exclues. |
| `GET /admin/fraud/flags`, `GET /admin/fraud/flags/{id}`, `PATCH /admin/fraud/flags/{id}` | Lecture et transitions de statut autorisées; pas de création de signalement, d'accès WatchSession ou de mutation de compte. |
| `GET /admin/raffles?page=1&limit=20`, `GET /admin/raffles/{id}`, `GET /admin/raffles/{id}/history` | Liste, fiche de configuration et audit; pagination et historique bornés. |
| `POST /admin/raffles`, `PATCH /admin/raffles/{id}` | Crée/édite un tirage ouvert et sa liste complète de lots; hash d'engagement, validation dates et HTTPS, sponsor existant; audit atomique. Le POST crée et publie également l'annonce programmée, dans la même transaction. |

La migration `0009_admin_raffle_configuration` contient la configuration des
tirages et lots; `0010_scratch_and_raffle_draws` ajoute les participations,
résultats et gagnants. Les réponses Admin exposent les compteurs persistés et
les états `scheduled`, `available`, `closed`, `drawn` pour chaque tirage ainsi
que leurs agrégats de liste. Une liste vide rapporte `unavailable`.
Les contrôles Admin ciblés rapportés incluent les refus anonyme/Viewer,
l'atomicité et les migrations sous SQLite; ils ne démontrent pas le verrouillage
concurrent PostgreSQL. Le build frontend passe selon le spécialiste; les
captures responsive, interactions clavier/modal, audit indépendant, CI et
fusion de #8 restent en attente.

## Récompenses et tirages Viewer, issue #9

Les règles sont mappées au code V1 épinglé `fcc4767f3ece9efc069d1a1c413942067cb89c93`:
`scratch-cards.service.ts`, son test `scratch-card-no-win.e2e-spec.ts`,
`raffles.controller.ts`, `raffles.service.ts`, `raffle-draw.ts`, `tirage.ts`,
`admin-raffles.controller.ts` et `dto/create-raffle.dto.ts`. D-07 et D-14 à
D-16/D-20 arbitrent les écarts V2. Les catégories `CLASSIC`/`PREMIUM` sont
uniquement des tickets à gratter; la participation est une entité distincte
`raffle_tickets`.

| Méthode et route | Contrat implémenté |
| --- | --- |
| `GET /me/scratch-cards`, `GET /me/reward-tickets`, `GET /me/scratch-history` | Inventaires et historique authentifiés, paginés; l'inventaire ne révèle jamais un résultat. |
| `POST /me/scratch-cards/{id}/prepare`, `POST /me/scratch-cards/{id}/scratch` | Préparation sans fuite de résultat puis révélation V1 persistée une seule fois; gains V1 70/25/5, ticket réorienté vers `RewardTicket` CLASSIC selon D-16, jamais vers `RaffleTicket`. |
| `POST /me/reward-tickets/{id}/prepare`, `POST /me/reward-tickets/{id}/scratch` | Résultats D-07 CLASSIC persistés avec ledger/ticket atomiques. Les tickets PREMIUM sont temporairement non grattables jusqu'à la décision propriétaire sur le résultat « accès au concours » à 1 %; refus 409 avant RNG, sans mutation ni reroll. |
| `POST /me/raffles/{id}/register`, `GET /me/raffle-tickets` | Achat d'une participation pour 2 500 points et journal atomiques, une entrée par user/tirage, retry stable; liste personnelle paginée. |
| `GET /raffles`, `GET /raffles/{id}`, `GET /raffles/{id}/result`, `GET /raffles/{id}/participants?page=0&taille=500` | Vues publiques; résultat et participants accessibles après tirage seulement. Résultat pseudonymisé; participants limités aux ticket IDs, pagination 0-based plafonnée à 2 000. |
| `POST /admin/raffles/{id}/draw`, `GET /admin/raffles/{id}/history` | Admin persisté, origine autorisée, engagement SHA-256 vérifié, date de tirage atteinte; gagnants, empreinte, résultat et audit écrits atomiquement. La graine dérivée suit V1 `SHA256(graineExploitant:entropiePublique)` et l'algorithme déterministe, sans biais modulo, sans remise. V2 rejoue le résultat stocké seulement si la graine et l'entropie correspondent; l'engagement de graine est comparé en temps constant, les entrées différentes reçoivent 409 et le tirage n'est jamais relancé. V1 répondait 409 à tout second appel. |

L'origine de l'entropie publique n'est pas spécifiée dans V1: l'UI ne doit
pas en générer une. Les champs de tirage sont fournis par l'Admin (1 à 512
caractères), le seed opérateur n'est pas persisté et les réponses publiques
n'exposent ni e-mail ni identifiant utilisateur.
