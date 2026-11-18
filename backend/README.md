# API Skkup V2

Service FastAPI de l’API Skkup V2. Alembic applique les changements de schéma;
le service ne crée pas automatiquement les tables.

Mise à jour : 2026-11-18.

État des lots : #5 Auth/session et #6 points/progression sont livrés dans
`dev`. Le lot Admin #8 est implémenté sur une branche de travail et reste en
revue avant livraison. Aucun déploiement public n’est documenté ou autorisé.

## Authentification membre

Le lot initial d’authentification conserve les routes et formes de réponse de
la V1 :

- `POST /auth/register` : `{ "email", "pseudo", "motDePasse", "accepteReglement" }`; renvoie `201 { "pseudo" }` et pose le cookie de session.
- `POST /auth/login` : `{ "email", "motDePasse" }`; renvoie `200 { "pseudo" }` et pose le cookie de session.
- `GET /auth/session` : renvoie `{ "authentifie": false, "profil": null }` sans session; sinon, renvoie le profil public du compte.
- `POST /auth/logout` : renvoie `204`, révoque la session courante si elle est valide et efface le cookie, même si la session est invalide.
- `PATCH /auth/password` : `{ "ancienMotDePasse", "nouveauMotDePasse" }`; renvoie `204`, modifie le hash et révoque toutes les sessions web.

L’inscription exige un mot de passe d’au moins 12 caractères comprenant une
minuscule, une majuscule, un chiffre et un caractère non alphanumérique. Le
changement de mot de passe suit le DTO V1 : 12 caractères, une minuscule, une
majuscule et un chiffre; le symbole n’est pas obligatoire. L’inscription
exige l’acceptation explicite du règlement. Les comptes sont créés avec le
rôle `VIEWER`; le client ne peut pas choisir un rôle. La récupération du mot
de passe et la vérification d’adresse e-mail ne sont pas implémentées, car
aucun parcours e-mail n’a été accepté. Les corps de requête invalides
renvoient HTTP 400 avec des messages français limités aux champs concernés;
les valeurs de requête et les mots de passe ne sont jamais renvoyés. La
formulation exacte des messages V1 reste à comparer aux sources.

Les mots de passe utilisent l’implémentation `scrypt` fournie par Python,
sans ajouter de dépendance à ce socle minimal. Il s’agit d’une base V2
réversible; les hashes de mots de passe V1 ne sont ni importés ni migrés. Les
sessions web utilisent une forme de jeton signé HS256 compatible V1 et une
ligne `auth_sessions` en base afin que l’API puisse appliquer immédiatement
la déconnexion, les changements de mot de passe et l’expiration. Le champ
`jourConnexion` du jeton est comparé au jour civil `Europe/Paris`; le jeton
devient invalide à minuit dans ce fuseau, même si son `exp` de 24 heures n’est
pas atteint. Cela correspond au contrôle du jour civil dans
`JwtStrategy.validate` de la V1 au commit
`fcc4767f3ece9efc069d1a1c413942067cb89c93`. Le règlement V1 mentionne
`Europe/Paris`, mais les fichiers Compose et Docker versionnés de la V1 ne
fixent pas le fuseau du serveur; celui utilisé historiquement ne peut donc pas
être établi à partir du dépôt. V2 définit `TZ=Europe/Paris` pour l’API et
inclut `tzdata` dans l’image d’exécution. Toutes les instances de l’API
doivent conserver ce fuseau. Le secret de signature n’est jamais stocké dans
le dépôt.

## Configuration

L’API nécessite les variables PostgreSQL `DB_HOST`, `POSTGRES_DB`,
`POSTGRES_USER` et `POSTGRES_PASSWORD`. L’authentification exige aussi
`AUTH_TOKEN_SECRET` d’au moins 32 octets. Définis `AUTH_ALLOWED_ORIGINS` comme
une liste exacte d’origines séparées par des virgules. La valeur de
développement par défaut est
`http://localhost:3010,http://127.0.0.1:3010,http://localhost:3000,http://127.0.0.1:3000`,
pour couvrir le port web local du dépôt et les ports de développement directs
courants. Les requêtes d’authentification qui modifient l’état doivent
présenter une valeur `Origin` autorisée; CORS n’autorise les cookies et autres
justificatifs d’authentification que pour ces origines.

Génère une clé locale de signature dans le shell avant de démarrer l’API, puis
transmets-la à l’environnement du processus. Ne la committe pas :

```bash
export AUTH_TOKEN_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

Compose exige cette variable et la transmet au conteneur API. Il transmet
également `AUTH_ALLOWED_ORIGINS` et une valeur explicite pour `COOKIE_SECURE`.
Pour une session HTTP locale, utilise `.env.example` comme modèle et définis
`COOKIE_SECURE=false`; ne garde pas ce réglage derrière une adresse HTTP
publique. Le client d’authentification envoie `credentials: "include"`.
Ouvre le site local à `http://localhost:3010` pour que son origine API par
défaut `http://localhost:8000` reste sur le même site pour le cookie Lax.
L’origine `http://127.0.0.1:3010` est autorisée par CORS, mais l’application web
appelle encore `localhost:8000` par défaut; mélanger les deux formes d’hôte
peut amener le navigateur à omettre le cookie Lax. Avant d’affirmer que les
deux variantes fonctionnent de bout en bout, une évolution du client ou de la
configuration d’exécution devra choisir le même nom d’hôte des deux côtés.

`COOKIE_SECURE` vaut `true` par défaut et configure le cookie
`__Host-vr_session` avec `Secure`, `HttpOnly`, `SameSite=Lax` et `Path=/`.
Pour le développement HTTP local seulement, définis `COOKIE_SECURE=false`;
le cookie devient alors `vr_session`, car les navigateurs refusent les
cookies `__Host-` sans `Secure`.

Les limitations d’authentification sont appliquées dans chaque processus et
comptent les requêtes par adresse cliente directe : 5 inscriptions par heure,
10 tentatives de connexion par minute et 3 changements de mot de passe par
heure. Ce mécanisme protège un processus sans Redis ni service additionnel. Il
n’est pas partagé entre processus, conteneurs ou redémarrages; avant toute
exposition publique ou exécution avec plusieurs processus de l’API, il faut utiliser un
limiteur partagé.

## Points et progression Viewer

Les routes de l’API du lot #6 utilisent le cookie de la session courante; elles
n’acceptent jamais un identifiant utilisateur fourni dans le corps ou la
requête :

- `GET /me` conserve la forme de réponse du profil V1.
- `GET /me/points` renvoie le solde de points, la série actuelle et maximale, le prochain palier de série documenté et le nombre de tickets à gratter `CLASSIC`/`PREMIUM` disponibles.
- `GET /me/points/history?page=1&limit=20` renvoie l’enveloppe de pagination V1 et les noms de champs des transactions, filtrés sur le Viewer authentifié.
- `GET /me/reward-tickets?page=1&limit=20` liste les tickets à gratter `CLASSIC`/`PREMIUM` non consommés; ils ne sont pas des participations aux tirages.
- `POST /me/daily-checkin` utilise l’identité de session et exige une origine `Origin` autorisée. Une requête répétée au cours du même jour civil `Europe/Paris` renvoie une réponse stable.

La décision D-14 remplace le crédit direct V1 de +5 points à la connexion
quotidienne par un ticket à gratter `CLASSIC`; cette connexion n’écrit
donc aucune entrée dans le registre de points. D-15 ajoute +1 ticket `CLASSIC` au jour de
série 3, +2 `CLASSIC` au jour 7, +2 `CLASSIC` et +1 `PREMIUM` au jour 14, puis
+2 `CLASSIC` et +2 `PREMIUM` au jour 30. Ces gains s’ajoutent au ticket
`CLASSIC` quotidien. Les catégories `CLASSIC` et `PREMIUM` désignent des
tickets à gratter, pas des participations aux tirages. Les droits de cartes à gratter des jours de série 3, 7,
14 et 30, déjà présents dans la V1, sont enregistrés atomiquement comme des
droits disponibles. Le résultat `TICKET` présélectionné par la V1 pour les
cartes accordées aux multiples de 10 après le jour 30 est conservé comme
métadonnée du droit débloqué, sans ajouter les tickets D-07.

Aucun résultat de grattage n’est choisi dans ce lot. Selon D-16/D-20, le gain
« ticket » d’une carte à gratter attribue en V2 un ticket à gratter `CLASSIC`
si un tirage est ouvert; sinon, le fallback points observé en V1 est conservé
selon D-08. Le code V1 attribuait sous cette condition une entrée `raffleTicket`,
ce qui diffère explicitement du type d’entité V2. Les tickets à gratter
`reward_tickets` et les participations `raffleTicket` restent deux entités
distinctes; #6 ne les consomme pas et n’implémente aucun achat. « Accès au
concours » est également un résultat distinct, et toute participation effective
au tirage relève de `raffleTicket`.

Les changements de points utilisent un registre transactionnel avec des
montants signés, le solde après modification et une clé d’idempotence par
utilisateur. Les événements à zéro point restent représentables pour
conserver les résultats de cartes V1. Le solde du compte et la ligne du
registre sont écrits dans la même transaction; les soldes négatifs sont
refusés et aucun plafond global ou quotidien n’est ajouté. Le registre et
l’inventaire des tickets restent séparés pour ne pas confondre un ticket avec
des points.

Pour rendre la connexion quotidienne idempotente, V2 utilise un événement unique
`(user_id, local_day)`, verrouille la ligne de l’utilisateur pendant
l’opération et valide ensemble la série, le droit de carte et les tickets.
Une requête répétée renvoie les identifiants de ticket et de carte déjà
enregistrés sans attribuer de nouvelle récompense. Cela diffère de la réponse
HTTP 409 envoyée par la V1 lors d’une connexion quotidienne en double, tout en
conservant l’unicité des gains et la sûreté des nouvelles tentatives. La table `scratch_card_grants`
stocke uniquement des droits; elle ne contient ni résultat ni état
d’animation. Ces mécaniques relèvent de l’issue #9.

## Administration, issue #8

Les routes Admin exigent une session web persistée valide et relisent
`users.role` en base à chaque requête. Une session absente, expirée, révoquée
ou inactive reçoit HTTP 401; un rôle Viewer reçoit HTTP 403. Les mutations
Admin exigent aussi un en-tête `Origin` autorisé.

- `GET /admin/users?search=...` renvoie jusqu’à 100 utilisateurs, du plus récent au plus ancien. La recherche sans casse porte sur le pseudo ou l’adresse e-mail.
- `GET /admin/users/{id}` renvoie le profil utilisateur et le nombre de transactions disponibles.
- `GET /admin/users/{id}/audit` renvoie les 100 derniers événements de statut de cet utilisateur.
- `PATCH /admin/users/{id}/status` accepte uniquement `{ "actif": boolean }`. La désactivation incrémente `session_version`, révoque les sessions web persistées et enregistre l’acteur ainsi que les états précédent et suivant dans la même transaction. Un Admin ne peut pas désactiver son propre compte. La réactivation ne restaure pas les sessions révoquées; le compte doit se reconnecter.

La modification des rôles n’est pas exposée. La décision D-11 laisse le
provisionnement initial d’un compte Admin en dehors de l’interface; ces routes
ne créent pas de compte Admin. Les réponses de liste et de fiche utilisateur
conservent les clés V1 `_count.raffleTickets` et `_count.watchSessions`, mais
leur valeur est `null` tant que ces domaines Viewer distincts ne sont pas
implémentés. L’inventaire des tickets de récompense n’est pas utilisé à la
place des entrées de tirage. Les indicateurs de synthèse et les opérations de
boutique constituent d’autres tranches de l’issue #8.

Les opérations sur les annonces et les contenus éditoriaux exigent une
session Admin persistée et une origine autorisée pour toute mutation :

- `GET/POST /admin/announcements` liste ou crée des annonces `DRAFT`. `PATCH /admin/announcements/{id}` modifie le texte ou la programmation; `actif: true` publie et `actif: false` archive. `POST /admin/announcements/{id}/publish`, `DELETE /admin/announcements/{id}` et `POST /admin/announcements/{id}/restore/{eventId}` offrent des transitions explicites. `GET /admin/announcements/{id}/history` renvoie les événements d’audit récents. `GET /announcements/active` ne renvoie que les annonces publiées dont la période est active.
- `GET/POST /admin/content` liste ou crée des enregistrements avec les champs V1 vérifiés `slug`, `type`, `locale` et le JSON de premier niveau `data`. Les types sont `LANDING`, `LEGAL`, `ANNOUNCEMENT`, `FAQ` et `MEDIA`; les langues sont `fr` et `en`. Le JSON imbriqué reste opaque, car aucune structure éditoriale plus détaillée n’est vérifiée.
- `GET/PATCH /admin/content/{id}`, `POST /admin/content/{id}/publish`, `GET /admin/content/{id}/history` et `POST /admin/content/{id}/restore/{version}` permettent de consulter, modifier, publier et restaurer une version. Une modification significative ajoute une version et un événement d’audit lié à son acteur dans la même transaction. Modifier un contenu publié le repasse à `DRAFT`, jusqu’à sa nouvelle publication.
- `GET /content/{type}/{locale}/{slug}` sert un enregistrement uniquement lorsqu’il est `PUBLISHED`; un brouillon est renvoyé comme introuvable.
- `GET /admin/sponsors?page=1&limit=100` renvoie les sponsors par nom, avec pagination bornée. `POST /admin/sponsors` accepte `{ "nom", "logoUrl"? }`; `PATCH /admin/sponsors/{id}` accepte `nom`, `logoUrl` (avec `null` pour l’effacer) et `actif`, tous facultatifs. Les URLs de logo doivent utiliser HTTPS et ne peuvent pas inclure d’identifiants. Ce sont les seules routes sponsor V1 vérifiées; aucune suppression n’est offerte. La création ou modification du sponsor et son événement d’audit sont validés ensemble. La liste conserve la clé V1 `_count.lots` à `null`; cette tranche ne calcule pas ce nombre, bien que la migration 0009 stocke maintenant la configuration des lots.

`GET /admin/dashboard/summary` est une lecture Admin bornée pour le cockpit.
Elle renvoie des compteurs basés sur la base ainsi que jusqu’à 8 événements
d’audit récents, 5 annonces publiées et 5 contenus publiés. Une carte
`availability` indique explicitement `not_implemented` pour les synthèses de
tirages, lots, signalements de fraude et streams qui ne sont pas disponibles
dans ce cockpit; leurs compteurs et sections de lignes valent `null`. Ainsi,
une donnée non disponible ne se confond pas avec un vrai zéro. Les champs de
réponse de l’audit sont sélectionnés explicitement; les métadonnées
d’événement et les secrets de compte sont exclus.

`GET /admin/audit?page=1&limit=20` expose la chronologie d’audit globale avec
pagination (100 événements maximum par page). Elle ne renvoie que l’identifiant,
l’action, l’entité, l’horodatage, l’identifiant et le pseudo de l’acteur; les
métadonnées brutes, l’adresse e-mail et les secrets de compte sont exclus. La
migration `0007_admin_audit_timeline` ajoute l’index décroissant de la
chronologie. La route est en lecture seule et réservée aux Admins.

La modération des `FraudFlag` utilise `GET /admin/fraud/flags?statut=` et
`GET /admin/fraud/flags/{id}`, avec des pages limitées à 100 éléments. Seuls
les statuts persistés `OUVERTE`, `EXAMINEE` et `IGNOREE` sont autorisés.
`PATCH /admin/fraud/flags/{id}` accepte uniquement `{ "statut", "note"? }`;
le statut, l’horodatage de revue et l’événement d’audit lié à l’acteur sont
validés ensemble. Cette route ne modifie pas le compte, ne crée pas de
signalement et ne déclenche aucun producteur. Aucun code V1 vérifié ne
précise le sens des champs libres `type` et `details`; ils sont conservés pour
la compatibilité avec le contrat d’origine, mais ne sont pas renvoyés par l’API. L’adresse e-mail
et les identifiants de session sont également omis. Les détails liés à
`WatchSession` restent indisponibles jusqu’à l’ajout de ce modèle dans le
lot #7; la migration `0008_admin_fraud_flags` ne comporte volontairement pas
de colonne ni de clé étrangère de session. Le limiteur courant autorise 60
requêtes Admin par minute et par compte/adresse client dans un seul processus;
une exécution avec plusieurs processus de l’API nécessite un limiteur partagé.

La configuration Admin des tirages est exposée par
`GET /admin/raffles?page=1&limit=20`, `GET /admin/raffles/{id}` et
`GET /admin/raffles/{id}/history`; la liste est limitée à 100 éléments et
l’historique à 100 événements. `POST /admin/raffles` exige `titre`,
`description`, `dateOuverture`, une `dateTirage` postérieure, l’engagement
SHA-256 `engagementGraine` de 64 caractères hexadécimaux et au moins un lot.
La route crée le tirage, ses lots, l’annonce publiée et programmée selon le
flux V1, ainsi que leurs événements d’audit dans une transaction. La graine
brute n’est jamais acceptée ni stockée. `PATCH /admin/raffles/{id}` peut
modifier uniquement `titre`, `description`, `dateTirage` et la liste complète
des lots, et seulement lorsque le statut du tirage est `OUVERT`. Les URLs des
images de lots doivent utiliser HTTPS; les identifiants de sponsor doivent
référencer un sponsor existant. Les valeurs `null` et une liste vide de lots
sont refusées. La modification remplace toute la liste de lots dans une
transaction; la ligne du tirage est verrouillée par les bases qui prennent en
charge les verrous de ligne. Les entrées d’audit contiennent les
configurations précédente et résultante. Il n’existe pas de route V1 ni V2
distincte pour supprimer un lot.

La réponse de configuration du tirage ne renvoie que la configuration et
l’engagement. Elle ne contient jamais la graine secrète ni les résultats;
`ticketsDistribues` et `gagnantsCount` donnent les nombres persistés. Les
champs `drawAvailability` et `ticketsAvailability`, ainsi que les agrégats
`availability.draws`/`availability.tickets` de la liste, reflètent les états
`scheduled`, `available`, `closed` ou `drawn`; une collection vide indique
`unavailable`. L’historique renvoie les événements et l’audit du tirage avec
`availability.draws` calculé depuis son état actuel.

## Récompenses et tirages Viewer, issue #9

Les tickets `reward_tickets` `CLASSIC` et `PREMIUM` sont exclusivement des
tickets à gratter. Ils ne sont jamais des entrées de concours. Les
participations achetées sont des `raffle_tickets` séparés, une par utilisateur
et tirage comme dans V1.

- `GET /me/scratch-cards` liste les droits de carte V1 non grattés; les
  résultats ne sont jamais inclus. `POST /me/scratch-cards/{id}/prepare`
  marque l’ouverture de la modale sans révéler de gain et
  `POST /me/scratch-cards/{id}/scratch` applique le résultat une seule fois.
- `GET /me/reward-tickets` liste l’inventaire disponible. Les mêmes routes
  `/me/reward-tickets/{id}/prepare` et `/scratch` gèrent les tickets D-07.
  `GET /me/scratch-history` expose les résultats effectivement révélés,
  paginés, avec date, catégorie, gain et montant. Préparation et grattage
  exigent une origine autorisée et une session; la persistance du résultat,
  du crédit au ledger et des tickets éventuellement attribués est atomique.
- CLASSIC applique les plages entières 0–29 rien, 30–44 +5, 45–54 +10,
  55–59 +15 et 60–99 un nouveau ticket à gratter CLASSIC. Les valeurs sont
  calculées par `secrets.randbelow(100)` et les tests injectent un RNG local,
  non exposé par l’API.
- PREMIUM reste verrouillé avant le RNG jusqu’à décision propriétaire sur le
  résultat « accès au concours » à 1 %. Aucun résultat différé n’est inventé.
- Les anciennes cartes de série gardent le tirage V1 70 % points, 25 % rien,
  5 % ticket, avec gains 10/15/25/40 par palier (10 par défaut). Selon D-16,
  le résultat ticket ajoute un ticket à gratter CLASSIC si un tirage est
  ouvert, jamais une participation `raffle_tickets`; sans tirage ouvert, le
  fallback points V1 s’applique.
- `POST /me/raffles/{id}/register` exige une session et une origine autorisée.
  Il débite 2 500 points via le ledger et crée la participation dans la même
  transaction; une nouvelle tentative renvoie la participation déjà achetée
  sans double débit. Une inscription par utilisateur/tirage est imposée par
  contrainte unique.
- `GET /me/raffle-tickets` fournit l’historique personnel paginé.
  `GET /raffles`, `/raffles/{id}`, `/raffles/{id}/result` et
  `/raffles/{id}/participants` fournissent les vues publiques. Le résultat et
  la liste ne paraissent qu’après le tirage. Les gagnants sont identifiés par
  pseudo et ticket; la liste publique contient uniquement les identifiants de
  tickets, jamais d’e-mail ni d’identifiant utilisateur. La pagination des
  participants suit V1: `page` commence à zéro, `taille` vaut 500 par défaut
  et est limitée à 2 000.
- `POST /admin/raffles/{id}/draw` exige Admin persistant et origine autorisée,
  refuse une date non atteinte, vérifie l’engagement SHA-256 de la graine
  exploitant, verrouille le tirage, puis écrit statut, gagnants, résultat et
  audit en transaction. Les champs `graineExploitant` et `entropiePublique`
  acceptent 1 à 512 caractères comme dans le DTO V1. L’interface Admin demande
  ces valeurs; elle ne fabrique pas une prétendue entropie publique. Le seed
  de résultat est SHA-256 de `graineExploitant:entropiePublique`; la sélection
  déterministe V1 trie les tickets, échantillonne sans remise et rejette les
  valeurs hors plage pour éviter un biais modulo. Le seed opérateur n’est pas
  stocké; le seed dérivé public, l’empreinte de participants et les gagnants
  permettent le rejeu.

  Si une requête `draw` est répétée après le passage à `TIRE`, V2 renvoie le
  résultat déjà enregistré uniquement lorsque graine exploitant et entropie
  publique correspondent aux entrées du tirage persisté. L’engagement de la
  graine est comparé en temps constant; la graine brute n’est pas conservée.
  Des entrées différentes reçoivent 409 et ne changent aucun état. Aucun retry
  ne relance le tirage. V1 répondait 409 à tout second appel; ce retry exact
  est un durcissement V2.

La migration `0010_scratch_and_raffle_draws` ajoute les états de grattage, les
participations distinctes, gagnants et audit du tirage. Aucune promotion vers
`main` ou activation publique n’est impliquée par ces routes.

L’application web V2 actuelle ne contient pas de rendu de script JSON-LD ni de puits
`dangerouslySetInnerHTML`. Si un rendu FAQ de ce type est ajouté, il devra
échapper `<` lors de la sérialisation du contenu éditable dans un élément
script et tester une charge `</script>`. Le stockage JSON dans l’API ne rend
pas l’insertion HTML ou script sûre. Les lectures publiques renvoient le JSON
enregistré et ne nettoient ni ne rendent le HTML.

Le shell partagé `/dashboard` sépare les sections Viewer et Admin d’après le
rôle de session vérifié côté serveur. L’interface Admin Raffles/Lots utilise
un parcours compact en modales pour la liste, le détail, l’historique, la
création et la modification; elle n’expose ni l’exécution du tirage ni
l’attribution des participations au tirage, distinctes des tickets à gratter
`CLASSIC`/`PREMIUM`. La vérification responsive et clavier du rendu
final reste une porte de livraison pour l’issue #8.

## Migrations

Après avoir défini l’environnement de base de données, applique le schéma
avec la configuration Alembic du dépôt. La migration `0002_member_auth` crée
les tables `users` et `auth_sessions`; `0003_viewer_points` ajoute le registre
de points, les connexions quotidiennes idempotentes, les événements
d’attribution des cartes à gratter et l’inventaire de tickets de récompense.
`0004_admin_user_audit`
ajoute les événements d’audit Admin indexés et liés à leur acteur.
`0005_admin_editorial` ajoute les annonces, les contenus typés et localisés
ainsi que des instantanés immuables de versions. `0006_admin_sponsors` ajoute
le catalogue sponsor de référence et son index d’activité.
`0007_admin_audit_timeline` indexe la chronologie globale.
`0008_admin_fraud_flags` ajoute les signalements liés aux utilisateurs sans
lien vers `WatchSession`, réservé au lot #7.
`0009_admin_raffle_configuration` ajoute la configuration Admin des tirages
et des lots sans champs de résultat du tirage. Chaque migration peut être
annulée avec son opération de retour arrière.

Ces migrations s’appliquent à la base V2 vide et n’importent ni ne modifient
les données V1 ou de production.

## Vérifications des contrats de l’API

Depuis la racine du dépôt, lance les contrôles de contrats API sans
dépendance externe :

```bash
PYTHONPATH=backend uv run --project backend --locked --no-sync python -m unittest discover -s backend/tests -p 'test_*.py'
```

Ces contrôles interrogent l’application FastAPI ASGI et ses routes de service
avec SQLite en mémoire. Ils couvrent la validation des requêtes,
l’inscription et son consentement, les cookies de session, le profil Viewer,
les erreurs de connexion, la révocation à la déconnexion et au changement de
mot de passe, la validation exacte d’`Origin`, le préflight CORS avec
authentification par cookie, l’idempotence des récompenses quotidiennes, les catégories
D-14/D-15, la catégorisation D-16 du ticket de grattage, la cohérence entre
registre et solde, les retours arrière transactionnels et l’unicité
utilisateur/jour. Les contrôles Admin des utilisateurs et contenus couvrent
le refus des requêtes anonymes et Viewer sur les routes protégées, la
revalidation du rôle en base, l’origine autorisée des mutations, le refus de
l’auto-désactivation, la révocation des sessions web, le cycle de vie des
annonces, la lecture des seuls contenus publiés, le versionnement et la
restauration des contenus, l’autorisation des routes sponsor, la validation
HTTPS des URLs, l’atomicité des audits, la confidentialité et la pagination
du journal global, les transitions de statut `FraudFlag`, la minimisation des
champs sensibles, l’absence d’effet de bord après un refus et la réversibilité
des migrations. Ces tests ne remplacent pas une vérification de migration ou
de concurrence sur PostgreSQL, ni les contrôles navigateur et visuels.

Les tranches serveur #5, #6 et #8 implémentées sont couvertes par cette
commande. Ruff doit être exécuté sur `backend/app`, `backend/migrations` et
`backend/tests`. Les contrôles SQLite couvrent les retours arrière et la
contrainte d’unicité du jour. Le verrouillage PostgreSQL réellement concurrent
et l’application des migrations par Compose restent des contrôles CI ou
d’environnement. Ces tests de contrat ne couvrent pas les formulaires, la
navigation, le clavier ni les captures d’écran.

## Limites actuelles

- Le changement de mot de passe incrémente `session_version` et révoque toutes
  les sessions web V2. La V1 révoque aussi les appairages d’extension actifs,
  les jetons d’appairage non utilisés et les sessions de visionnage actives.
  V2 n’a pas encore ces tables; cette révocation complète attend donc le lot
  #7. Tout futur identifiant d’extension devra porter l’époque
  `session_version` du compte et la faire vérifier par le serveur à chaque
  requête. La révocation des appairages et l’invalidation des sessions de
  visionnage restent explicitement au lot #7.
- `SameSite=Lax` et la validation exacte d’`Origin` forment la protection
  initiale contre les requêtes intersites. La confiance accordée aux
  mandataires réseau, la configuration des origines en production et le
  comportement de l’application web qui envoie les cookies de session doit être
  vérifiés pendant l’intégration navigateur et le déploiement.
- Le validateur d’adresse e-mail à l’inscription et à la connexion effectue
  un contrôle syntaxique simple; il ne couvre pas l’ensemble de la
  spécification RFC des adresses. Il faut comparer les champs et messages V1
  acceptés avant de revendiquer une parité complète de validation.
- La session expire après 24 heures, conformément à la durée du cookie et du
  jeton V1.
