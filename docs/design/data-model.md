---
status: draft
last_updated: 2026-11-18
owner: Coordinateur
work_item: 2026-11-18-chain-issues-5-6-8-9
---

# Modèle de données cible de Skkup V2

## Statut et niveau de preuve

Ce document propose un modèle conceptuel d’après le cahier actif et le
profil. Ce n’est ni un schéma SQL ni la preuve que les tables V1 ont été
vérifiées dans cette passe.

La migration #5 `0002_member_auth` crée les tables `users` et `auth_sessions`;
elle contient déjà `users.points_balance`, `current_streak`, `max_streak` et
`last_visit_at`. Le lot #6 réutilise ces colonnes. Sa migration
`0003_viewer_points` ajoute uniquement les tables `points_transactions`,
`daily_checkins`, `scratch_card_grants` et `reward_tickets`. Cette mise à jour
décrit les artefacts du code sur la branche #6. Les migrations `0004` à `0009`
ajoutent l’audit Admin, les annonces/contenus/versionnage, les sponsors, la
chronologie globale, les signalements de fraude et la configuration des
tirages/lots sur la branche de travail #8. Les tranches #5 et #6 sont
fusionnées dans `dev`; #8 attend encore sa revue finale et sa livraison. Les
contrôles rapportés pour #8 utilisent SQLite et ne certifient pas la migration
ou la concurrence sur PostgreSQL ni une parité complète avec le schéma V1. Les
tables d'appairage et de visionnage ne sont pas livrées dans #6 et restent au
lot #7.

### Sous-ensemble physique implémenté par le lot #6

- `points_transactions`: entrée signée avec `amount`, `balance_after`, `type`,
  clé d'idempotence et horodatage; unicité par utilisateur et clé, types
  autorisés par contrainte, index utilisateur/date. Le service verrouille le
  compte, refuse un solde négatif et modifie solde et ledger dans la même
  transaction.
- `daily_checkins`: date métier, streak après check-in, maximum, solde observé
  et indicateur de grant carte; contrainte unique par utilisateur/jour métier.
- `scratch_card_grants`: droit à une carte obtenu à un check-in de palier;
  unique par check-in. Il ne stocke pas de résultat de grattage ni d'état de
  révélation.
- `reward_tickets`: catégorie, origine, identifiant source, clé d'idempotence,
  date d'émission et éventuelle date de consommation; contraintes sur les
  catégories et origines ainsi qu'une unicité utilisateur/clé. Les catégories
  `CLASSIC` et `PREMIUM` représentent des tickets à gratter, pas des entrées de
  tirage. #6 n'implémente pas le grattage et ne transforme pas ces lignes en
  participations aux tirages.

Validation rapportée: QA indique 14 tests ciblés passés et Ruff PASS; les
tests couvrent l'isolation Viewer, replay quotidien, rollback, cohérence du
ledger et règles D-14 à D-16. Le test de migration vérifie le DDL et les
contraintes d'unicité avec SQLite. Ces éléments n'établissent pas la
concurrence multiprocessus PostgreSQL ni l'exécution de la migration sur
PostgreSQL. La livraison #6 reste sur sa branche en attente de PR/CI/fusion.
Dans l'interface, le Dashboard traduit les codes de type de transaction connus
en libellés français (par exemple `WATCH_TIME` en « Temps de visionnage »); le
contrat REST conserve le code dans le champ `type`.

- **Décisions de stack :** PostgreSQL, SQLAlchemy 2 et Alembic.
- **Décision de données :** démarrer sur une base V2 vide, sans migration
  implicite.
- **Référence à vérifier plus tard :** le cahier cite le schéma Prisma et ses
  migrations V1. Ils n’ont pas été relus dans cette passe.
- **Non déterminé par ce modèle :** durées de rétention, traitement des
  demandes de suppression/export, base légale et obligations applicables.

## Principes

1. PostgreSQL porte l’état durable des comptes, permissions, soldes, sessions,
   achats, stocks, tickets, tirages et contenus.
2. Les classes SQLAlchemy, schémas Pydantic et types TypeScript sont des
   représentations séparées reliées par les contrats d’API.
3. Alembic versionne les changements de schéma; les migrations n’importent
   aucune donnée de production par défaut.
4. Les invariants sont protégés par contraintes SQL et transactions, en plus
   des validations Python.
5. Le ledger et les événements d’audit gardent une trace explicable; un solde
   courant seul ne prouve pas un crédit ou un débit.
6. Les données sensibles sont minimisées, hachées ou chiffrées selon leur
   usage. Les secrets de chiffrement restent hors base et hors dépôt.

## Modèle conceptuel

```mermaid
erDiagram
    USER ||--o{ AUTH_SESSION : possède
    USER ||--o{ EXTENSION_PAIRING_TOKEN : demande
    USER ||--o{ EXTENSION_PAIRING : associe
    USER ||--o{ WATCH_SESSION : regarde
    USER ||--o{ POINTS_TRANSACTION : reçoit
    WATCH_SESSION ||--o{ POINTS_TRANSACTION : crédite
    USER ||--o{ SCRATCH_CARD : débloque
    USER ||--o{ REWARD_TICKET : possède (ticket à gratter)
    USER ||--o{ RAFFLE_TICKET : détient
    RAFFLE ||--o{ RAFFLE_TICKET : reçoit
    RAFFLE ||--o{ RAFFLE_LOT : propose
    SPONSOR o|--o{ RAFFLE_LOT : associe
    RAFFLE ||--o{ RAFFLE_WINNER : désigne
    USER ||--o{ SHOP_PURCHASE : effectue
    SHOP_ITEM ||--o{ SHOP_PURCHASE : concerne
    SHOP_ITEM ||--o{ SHOP_DIGITAL_CODE : stocke
    SHOP_PURCHASE ||--o| SHOP_DIGITAL_CODE : attribue
    USER ||--o{ MANAGED_CONTENT : rédige
    USER ||--o{ CONTENT_AUDIT_EVENT : réalise
```

Le diagramme exprime le périmètre logique. Les éléments Sponsor ci-dessous
sont vérifiés dans le schéma V1 au commit `76315fce9f27b957dcb68ce5b834367bb374046f`;
les autres noms physiques, colonnes, cardinalités et contraintes restent à
valider avant leur implémentation.

## Entités et règles attendues

| Domaine | Concepts | Invariants à concevoir | Sensibilité et limite |
|---|---|---|---|
| Comptes, état actuel du lot #5 | `users`, `auth_sessions`; `password_hash`, `session_version`, `terms_accepted_at`, dates et révocation | Email unique; Viewer par défaut; compte actif; session web expirée/révocable; rôle Admin non modifiable par le client. Le changement de mot de passe augmente `session_version` et révoque les sessions web V2. | Email et hash; ne jamais exposer le hash. scrypt pour le hash courant; aucun hash V1 importé |
| Appairage | Code temporaire, appareil apparié | Usage unique, expiration, révocation; concurrence de consommation protégée | Credential distinct de la session web; empreinte plutôt que valeur claire |
| Plateformes | Stream/catalogue, compte lié si nécessaire | Unicité plateforme + identifiant; désactivation sans perte d’historique utile | Aucun OAuth de plateforme ajouté dans ce périmètre |
| Visionnage | Session, heartbeats, durée validée | Mesure côté serveur; état contrôlé; pas de double crédit lors des retries | Activité à minimiser et rétention à définir |
| Points, sous-ensemble #6 implémenté | `points_transactions`, `users.points_balance` | Delta et ledger transactionnels, idempotence par utilisateur/clé, solde non négatif; aucun plafond global ajouté | Tests ciblés SQLite PASS; concurrence PostgreSQL non vérifiée |
| Check-in/progression, sous-ensemble #6 implémenté | `daily_checkins`, champs streak de `users`, `scratch_card_grants` | Unique par utilisateur/jour métier; replay renvoie le résultat stable; grants aux paliers appliqués selon D-08/D-15 | `TZ` configure la journée métier, `Europe/Paris` par défaut; migration/concurrence PostgreSQL non vérifiées |
| Cartes à gratter, grants seulement dans #6 | `scratch_card_grants` | Grant de palier unique par check-in; le résultat, sa révélation et le gain ne sont pas implémentés | À compléter au lot #9 avec D-08/D-16; un grant n’est pas encore un ticket jouable |
| Tickets à gratter disponibles, sous-ensemble #6 implémenté | `reward_tickets` | Émission catégorisée `CLASSIC`/`PREMIUM` et idempotente; inventaire de tickets à gratter non consommés | #6 ne réalise pas de grattage et ne crée pas d’entrée de tirage à partir de ces lignes; parcours de grattage en #9 |
| Tirages, configuration Admin #8 | `raffles`, `raffle_lots` et audit | Dates valides; création/édition transactionnelles; lots remplacés comme une liste complète; l’édition exige un tirage `OUVERT` | Migration `0009_admin_raffle_configuration`; les participations `raffle_tickets`, résultats, gagnants et exécution du tirage sont distincts des tickets à gratter et restent en #9 |
| Boutique | Article, commande, code numérique | Instantané de l’article acheté; idempotence; stock/limites/solde contrôlés; attribution atomique | Codes chiffrés au repos; clé externe et versionnée |
| Contenu | Annonce, contenu éditorial, version | Brouillon distinct de publication; archivage sans effacer l’historique requis | Données libres filtrées contre l’injection |
| Administration/risque | Signal antifraude, événement d’audit | Transition de statut contrôlée; acteur et horodatage traçables | Accès Admin limité; aucun secret dans les logs |

### Sponsor, preuve V1 et état V2

Le schéma V1 définit `Sponsor` avec `id`, `nom`, `logoUrl` facultatif,
`actif` par défaut à vrai et `createdAt`, plus un index sur `actif`. Chaque
`RaffleLot` peut référencer un sponsor via `sponsorId` facultatif; à la
suppression d'un sponsor, la clé du lot est mise à `NULL`. Ces éléments sont
vérifiés dans `backend/prisma/schema.prisma` du checkout frère `Skkup`, au
commit `76315fce9f27b957dcb68ce5b834367bb374046f`.

Le lot Admin V2 ajoute la table `sponsors` par la migration
`0006_admin_sponsors` et expose les routes V1 `GET`, `POST` et
`PATCH /admin/sponsors`. La migration `0009_admin_raffle_configuration` ajoute
`raffles` et `raffle_lots`; chaque lot référence un tirage et peut référencer
un sponsor, dont la suppression met la référence à `NULL`. La réponse Admin
des sponsors conserve `_count.lots: null` sans calculer ce décompte dans cette
tranche. La stratégie de snapshot d'un sponsor lié à un lot et les règles de
visibilité après publication ne sont pas définies ici.

### Configuration Admin des tirages et lots, issue #8

La migration `0009_admin_raffle_configuration` crée `raffles` et
`raffle_lots`. La configuration inclut titre, description, dates d’ouverture
et de tirage, statut et engagement SHA-256; un lot contient son nom, sa valeur
estimée, sa quantité positive, son fournisseur, une URL d’image facultative et
un sponsor facultatif. La relation tirage-lot cascade à la suppression du
tirage; la référence sponsor devient `NULL` si le sponsor est supprimé.

L’API Admin valide la configuration, refuse un engagement autre qu’un hash
hexadécimal de 64 caractères à la création, limite la modification aux
tirages ouverts et remplace la liste complète des lots en une transaction.
La création produit aussi l’annonce planifiée/publicée et les entrées d’audit
dans la même transaction, selon le flux V1 observé. Le PATCH verrouille la
ligne du tirage sur les bases qui prennent en charge les verrous de ligne; les
tests SQLite ciblés ne démontrent pas le comportement concurrent sur
PostgreSQL. La migration ne stocke ni graine secrète, ni résultat, ni gagnant.
L’issue #9 traite séparément les tickets Viewer `CLASSIC`/`PREMIUM` à gratter,
les entrées `raffle_tickets`, les résultats et les gagnants. Selon D-16/D-20,
le résultat « ticket » d’une carte à gratter attribue en V2 un ticket à gratter
`CLASSIC` lorsque le tirage est ouvert; sans tirage ouvert, le fallback points
observé dans V1 est conservé selon D-08. Le code V1 créait, pour le même
résultat et sous cette condition, une entrée de tirage `raffleTicket` : cette
différence de type d’entité est une décision V2 explicite. Les tickets
`reward_tickets` ne sont jamais consommés comme participation; toute entrée
effective au tirage relève de l’entité distincte `raffleTicket`.

Ces concepts viennent des sections fonctionnelles du cahier. Les concepts
`check-in`, `audit` et `fraude` doivent être rapprochés des règles actives et
du schéma de référence avant de fixer les relations physiques.

## Invariants transactionnels

- **Points :** ledger et solde/cache sont modifiés dans une même transaction,
  ou le solde est recalculable de façon reproductible.
- **Visionnage :** vérifier les intervalles côté serveur, appliquer bonus et
  plafond sans crédit multiple d’une session rejouée.
- **Carte :** consommer une fois; enregistrer le résultat et son crédit ou
  ticket atomiquement.
- **Achat :** vérifier article actif, stock et limites; écrire débit, commande,
  ledger et attribution comme une unité; utiliser une clé d’idempotence.
- **Ticket :** chaque émission est liée à un utilisateur et à un tirage sans
  double attribution.
- **Tirage :** la clôture et la sélection du gagnant ne s’exécutent qu’une
  fois; le résultat et son audit sont persistés ensemble.
- **Admin :** aucun endpoint d’auto-promotion; les changements sensibles sont
  audités.

Les contraintes, isolation, verrouillage et index exacts sont à choisir après
examen du schéma et des cas concurrents de la référence. Le présent document
ne prescrit pas de colonnes ou de code SQL.

## Classification et cycle de vie

| Classe | Exemples | Traitement à définir |
|---|---|---|
| Identité | Email, pseudo, rôle, hash | Minimisation, contrôle par compte, export/suppression |
| Credentials | Session, jeton d’extension, code, clé | Pas de valeur secrète en clair dans logs; empreinte, expiration, révocation, rotation |
| Comptabilité fonctionnelle | Points, commandes, tickets, gagnants | Historique cohérent; accès autorisé; conservation définie avant lancement |
| Activité | Heartbeats, durées, antifraude | Finalité, rétention et suppression/anonymisation à fixer |
| Contenu | Annonces, articles et versions | Séparer brouillon/publication et préserver l’historique utile |
| Configuration | Catalogue, récompenses, paramètres | Historiser les changements importants; secrets via mécanisme séparé |

Ce tableau ne vaut pas avis juridique et ne fixe pas de durée légale. Une
revue métier et conformité doit compléter la classification avant ouverture
publique.

## Base initiale, migration et sauvegarde

Le propriétaire a choisi la recommandation d’une base V2 vide, après
vérification des besoins de conservation. Cela exclut toute migration
automatique de comptes, soldes, historiques, codes, commandes, tickets ou
sessions dans le présent cadrage. Cela n’autorise ni suppression ni
modification de la production existante.

Avant création de base ou bascule, inventorier en lecture seule les éléments
à conserver; décider explicitement si contenu ou données de démonstration sont
recréés. Toute migration ultérieure exige un mapping séparé, copie anonymisée,
contrôle des soldes/relations, stratégie répétable et retour arrière.

Les migrations V2 passent par Alembic. Les sauvegardes/restaurations sont à
définir quand l’environnement cible sera choisi; la restauration isolée doit
vérifier ledger, commandes, stock, tickets et liens aux tirages. Aucun accès à
la production n’a été effectué pour ce document.

## Vérifications avant schéma physique

| Vérification | Source attendue | État dans cette passe |
|---|---|---|
| Tables, colonnes, relations, index et contraintes V1 | Commit du dépôt de référence cité dans le cahier, schéma et migrations | Non relu |
| Idempotence des points, cartes, achats et tickets | Code et tests V1 | Non vérifiée |
| Fuseau et frontière du check-in | `backend/app/timezone.py`, tests #6 et configuration `TZ` | Code: `Europe/Paris` par défaut, surcharge par `TZ`; frontière PostgreSQL/concurrence non vérifiée |
| Probabilités et valeurs de récompenses complémentaires | Règles actives et décisions du propriétaire | À extraire; ne pas inventer |
| Données de production à conserver | Inventaire en lecture seule et décision explicite | Non vérifié; pas de migration implicite |
| Rétention/export/suppression | Revue métier et conformité applicable | À définir avant activation publique |
| Volumes et index requis | Volumétrie et usage attendus | Aucun budget quantifié dans le cahier |

## Limites

Ce document conserve le modèle conceptuel pour les domaines à venir; les
entités marquées #6 décrivent le schéma SQLAlchemy/Alembic réellement présent
sur la branche de travail. Il ne prouve pas la parité V1, la migration ni la
concurrence sous PostgreSQL, et n'est pas une déclaration de conformité ou de
publication. Aucun jeu de données de production n’a été utilisé.
