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
décrit les artefacts du code sur la branche #6; elle ne certifie pas une
migration ou une concurrence en environnement PostgreSQL, ni une parité
complète avec le schéma V1. Les tables d'appairage et de visionnage ne sont
pas livrées dans #6 et restent au lot #7.

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
  catégories et origines ainsi qu'une unicité utilisateur/clé. #6 n'implémente
  pas encore la consommation dans un tirage.

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
    USER ||--o{ RAFFLE_TICKET : détient
    RAFFLE ||--o{ RAFFLE_TICKET : reçoit
    RAFFLE ||--o{ RAFFLE_LOT : propose
    RAFFLE ||--o{ RAFFLE_WINNER : désigne
    USER ||--o{ SHOP_PURCHASE : effectue
    SHOP_ITEM ||--o{ SHOP_PURCHASE : concerne
    SHOP_ITEM ||--o{ SHOP_DIGITAL_CODE : stocke
    SHOP_PURCHASE ||--o| SHOP_DIGITAL_CODE : attribue
    USER ||--o{ MANAGED_CONTENT : rédige
    USER ||--o{ CONTENT_AUDIT_EVENT : réalise
```

Le diagramme exprime le périmètre logique, pas la structure de la V1. Les
noms physiques, colonnes, cardinalités et contraintes seront validés en
relisant le commit de référence avant le scaffold.

## Entités et règles attendues

| Domaine | Concepts | Invariants à concevoir | Sensibilité et limite |
|---|---|---|---|
| Comptes, état actuel du lot #5 | `users`, `auth_sessions`; `password_hash`, `session_version`, `terms_accepted_at`, dates et révocation | Email unique; Viewer par défaut; compte actif; session web expirée/révocable; rôle Admin non modifiable par le client. Le changement de mot de passe augmente `session_version` et révoque les sessions web V2. | Email et hash; ne jamais exposer le hash. scrypt pour le hash courant; aucun hash V1 importé |
| Appairage | Code temporaire, appareil apparié | Usage unique, expiration, révocation; concurrence de consommation protégée | Credential distinct de la session web; empreinte plutôt que valeur claire |
| Plateformes | Stream/catalogue, compte lié si nécessaire | Unicité plateforme + identifiant; désactivation sans perte d’historique utile | Aucun OAuth de plateforme ajouté dans ce périmètre |
| Visionnage | Session, heartbeats, durée validée | Mesure côté serveur; état contrôlé; pas de double crédit lors des retries | Activité à minimiser et rétention à définir |
| Points, sous-ensemble #6 implémenté | `points_transactions`, `users.points_balance` | Delta et ledger transactionnels, idempotence par utilisateur/clé, solde non négatif; aucun plafond global ajouté | Tests ciblés SQLite PASS; concurrence PostgreSQL non vérifiée |
| Check-in/progression, sous-ensemble #6 implémenté | `daily_checkins`, champs streak de `users`, `scratch_card_grants` | Unique par utilisateur/jour métier; replay renvoie le résultat stable; grants aux paliers appliqués selon D-08/D-15 | `TZ` configure la journée métier, `Europe/Paris` par défaut; migration/concurrence PostgreSQL non vérifiées |
| Cartes, grant seulement dans #6 | `scratch_card_grants` | Grant de palier unique par check-in; le résultat, sa révélation et le gain ne sont pas implémentés | À compléter au lot #9 avec les décisions D-08/D-16; ne pas confondre grant et carte jouable |
| Tickets disponibles, sous-ensemble #6 implémenté | `reward_tickets` | Émission catégorisée et idempotente, inventaire des tickets non consommés | Consommation, tirages et résultats non implémentés; aucun lancement public |
| Tirages | Tirage, lot, ticket, gagnant et audit | Émission traçable; sélection unique; statut et résultat persistés ensemble | Résultat justifiable sans révéler de secrets |
| Boutique | Article, commande, code numérique | Instantané de l’article acheté; idempotence; stock/limites/solde contrôlés; attribution atomique | Codes chiffrés au repos; clé externe et versionnée |
| Contenu | Annonce, contenu éditorial, version | Brouillon distinct de publication; archivage sans effacer l’historique requis | Données libres filtrées contre l’injection |
| Administration/risque | Signal antifraude, événement d’audit | Transition de statut contrôlée; acteur et horodatage traçables | Accès Admin limité; aucun secret dans les logs |

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
