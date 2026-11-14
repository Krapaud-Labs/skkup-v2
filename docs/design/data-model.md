---
status: draft
last_updated: 2026-11-14
owner: Coordinateur
work_item: 2026-11-14-initialisation-cadrage-v2
---

# Modèle de données cible de Skkup V2

## Statut et niveau de preuve

Ce document propose un modèle conceptuel d’après le cahier actif et le
profil. Ce n’est ni un schéma SQL ni la preuve que les tables V1 ont été
vérifiées dans cette passe.

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
| Comptes | Utilisateur, session web | Email unique; Viewer par défaut; session expirée/révocable; rôle Admin non modifiable par le client | Email et hash; ne jamais exposer le hash |
| Appairage | Code temporaire, appareil apparié | Usage unique, expiration, révocation; concurrence de consommation protégée | Credential distinct de la session web; empreinte plutôt que valeur claire |
| Plateformes | Stream/catalogue, compte lié si nécessaire | Unicité plateforme + identifiant; désactivation sans perte d’historique utile | Aucun OAuth de plateforme ajouté dans ce périmètre |
| Visionnage | Session, heartbeats, durée validée | Mesure côté serveur; état contrôlé; pas de double crédit lors des retries | Activité à minimiser et rétention à définir |
| Points | Transaction de ledger, solde/cache éventuel | Crédit/débit atomique, traçable et idempotent; plafond journalier côté serveur | Barème selon les décisions acceptées, pas de valeur inventée |
| Visites/progression | Check-in, streak et paliers | Une visite par période qualifiée; transition atomique des paliers | Fuseau horaire/frontière de journée à confirmer sur les règles actives |
| Cartes | Carte à gratter et résultat | Révélation unique; résultat persisté avant retour; pas de double gain | Valeurs et probabilités depuis les règles validées |
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
| Fuseau et frontière du check-in/plafond quotidien | Règles métier et tests actifs | À confirmer |
| Probabilités et valeurs de récompenses complémentaires | Règles actives et décisions du propriétaire | À extraire; ne pas inventer |
| Données de production à conserver | Inventaire en lecture seule et décision explicite | Non vérifié; pas de migration implicite |
| Rétention/export/suppression | Revue métier et conformité applicable | À définir avant activation publique |
| Volumes et index requis | Volumétrie et usage attendus | Aucun budget quantifié dans le cahier |

## Limites

Ce modèle n’est pas le schéma final SQLAlchemy, une migration, une preuve de
parité avec la V1 ni une déclaration de conformité. Il devra être rapproché
du commit et des tests de référence avant le scaffold. Aucun code, actif ou
jeu de données de production n’a été utilisé.
