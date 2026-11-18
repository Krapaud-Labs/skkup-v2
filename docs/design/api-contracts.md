# Contrats d'interfaces

## Décisions et limites

API cible REST JSON/OpenAPI avec FastAPI/Pydantic. La compatibilité Socket.IO du client existant est à préserver jusqu'à l'inventaire des contrats et clients publiés. Les domaines ci-dessous sont des frontières de conception, pas des endpoints approuvés.

| Domaine | Consommateur | Responsabilité | Autorisation à spécifier | Preuve avant implémentation |
| --- | --- | --- | --- | --- |
| Authentification/session | site | ouvrir, terminer, consulter une session, changer le mot de passe | compte concerné, anti-abus, origine autorisée | 5 tests Auth et Ruff passent; comparaison visuelle V1/V2 effectuée sur captures, parité fonctionnelle complète et PostgreSQL/Docker en attente |
| Profil/activité | site | profil, solde, ledger, progression, inventaire des tickets | propriétaire du compte | #6: routes Viewer implémentées sur la branche feature; merge vers `dev` en attente |
| Appairage/visionnage | extension | lier appareil, envoyer activité admissible | jeton révocable | routes, payloads, plateformes |
| Récompenses/tirages | site | dépenser, tirer, historiser | rôle Viewer et états métier | transactions et auditabilité |
| Administration | dashboard Admin | gérer utilisateurs et contenus | rôle/ressource côté serveur | matrice d'accès et journal |
| Temps réel | site/extension | notifier changements | handshake, rooms isolées | protocole Socket.IO V1 |

## Conventions à décider au scaffold

Versionnement, erreurs, pagination, idempotence, tailles maximales, délais et retry seront spécifiés en cohérence avec les clients V1. Les réponses n'exposent pas l'existence d'un compte. L'API est la source de vérité des droits, soldes, durées créditées et états de tirage.

## Compatibilité

Ne pas changer les routes ou payloads consommés par l'extension sans versionnement et migration coordonnée. REST permet de récupérer l'état si le temps réel échoue. Les exemples concrets attendent la comparaison au commit V1.

## Points et progression Viewer, lot #6 en cours

Toutes les routes de cette section exigent une session web authentifiée. Les
résultats sont rattachés à l'identité de session; le client ne fournit pas le
`user_id` cible. Les routes sont présentes sur la branche de l'issue #6; la PR,
la CI et la fusion vers `dev` restent en attente.

| Méthode et route | Contrat implémenté |
| --- | --- |
| `GET /me` | Profil: `id`, `email`, `pseudo`, `role`, `soldePoints`, `streakActuel`, `streakMax`, `derniereVisiteAt`, `createdAt`. |
| `GET /me/points` | Résumé: `soldePoints`, `streakActuel`, `streakMax`, `derniereVisiteAt`, `prochainPalierStreak`, `ticketsDisponibles` par catégorie. Compare le solde utilisateur à la somme du ledger et renvoie HTTP 500 en cas de divergence. |
| `GET /me/points/history?page=1&limit=20` | Historique paginé, `limit` borné à 1–100; retourne `transactions` (`id`, `userId`, `type`, `montant`, `watchSessionId`, `shopPurchaseId`, `createdAt`), `page`, `limit`, `total`, `totalPages`. |
| `GET /me/reward-tickets?page=1&limit=20` | Inventaire paginé des tickets non consommés, limite 1–100; chaque ticket expose `id`, `categorie`, `origine`, `obtenuLe`, avec `page`, `limit`, `total`, `totalPages`. Cette route n'effectue ni consommation ni inscription à un tirage. |
| `POST /me/daily-checkin` | Sans payload métier; vérifie l'origine et la session. Enregistre au plus un check-in par journée métier et réexpose le même résultat lors d'un replay. Attribue le ticket quotidien Classic; applique les tickets additionnels de palier D-15 et crée les grants de cartes V1 aux paliers prévus. Réponse: `id`, `jourConnexion`, `streakActuel`, `streakMax`, `soldePoints`, `pointsCredites` (0), `ticketsAttribues[]`, `carteAGratterDebloquee`, `palierCarte` et `carteDebloquee` (ou `null`). |

Le jour métier utilise `TZ` avec `Europe/Paris` par défaut. Les décisions
D-14 à D-16 régissent la première récompense quotidienne et les tickets de
paliers. Les tests ciblés rapportés par QA couvrent l'isolation Viewer, le
replay quotidien, le rollback, le ledger et ces décisions; Ruff passe et la
migration DDL a été exercée sous SQLite. Ni migration PostgreSQL, ni test de
concurrence mult-processus sur PostgreSQL ne sont revendiqués. Le grant de
carte ne contient pas encore le résultat ou le mécanisme de grattage; ces
parcours et l'usage des tickets restent au lot #9.

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
