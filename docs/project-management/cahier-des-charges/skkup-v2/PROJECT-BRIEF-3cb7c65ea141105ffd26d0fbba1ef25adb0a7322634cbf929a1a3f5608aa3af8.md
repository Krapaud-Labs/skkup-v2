---
status: reconstructed
version: 2.0-draft
reference_repository: https://github.com/Krapaud-Labs/Skkup
reference_branch: dev
reference_commit: fcc4767f3ece9efc069d1a1c413942067cb89c93
last_updated: 2026-11-14
---

# Skkup V2 — cahier des charges provisoire

## 1. Statut et portée de ce document

Ce cahier des charges est une **reconstruction provisoire** à partir des
décisions données dans la conversation et du dépôt Skkup de référence. Il ne
remplace pas le cahier accepté de la V1 et ne vaut pas validation des choix
marqués « à confirmer ».

Le dépôt de référence est
[`Krapaud-Labs/Skkup`](https://github.com/Krapaud-Labs/Skkup), branche `dev`,
au commit `fcc4767f3ece9efc069d1a1c413942067cb89c93` au moment de la rédaction.
Le propriétaire demande que ce dépôt serve de référence concrète pour les
fonctionnalités, les règles métier, la vitrine, les images réellement utilisées
et l’interface de l’extension.

Le propriétaire indique que le site actuel est en production mais pas utilisé,
et donne carte blanche pour refaire le dashboard et la base technique. Cette
déclaration signifie qu’une migration sans interruption pour des utilisateurs
actifs n’est pas un objectif V2. L’existence de données à conserver reste à
vérifier avant toute création de base ou bascule.

## 2. Décisions déjà données par le propriétaire

- Construire Skkup V2 dans un **nouveau dépôt Git**, distinct du dépôt actuel.
- Reprendre le même périmètre fonctionnel que l’application actuelle, sans
  supprimer de fonctionnalité utilisateur ou administrateur.
- Refaire entièrement le dashboard Viewer et le dashboard Admin.
- Utiliser un backend **Python FastAPI**, **SQLAlchemy** et **PostgreSQL**.
- Utiliser **React avec TypeScript** pour l’interface.
- Utiliser **Docker** pour les environnements et les services V2.
- Conserver dans leur état actuel la vitrine, les seules images effectivement
  utilisées et le frontend de l’extension.
- Conserver les pages Connexion et Inscription avec un rendu visuel et des
  parcours visibles 100 % identiques à la V1; leurs appels d’authentification
  pourront être branchés sur le backend V2.
- Garder le dépôt actuel comme référence et ne pas le transformer en dépôt V2.

Ces décisions autorisent le cadrage documentaire. Elles n’autorisent pas encore
la création du dépôt, la copie d’éléments, la suppression de données, la
configuration d’un déploiement ou la bascule de production.

## 3. Définition de la parité fonctionnelle

« Les mêmes fonctionnalités » signifie que, avant de remplacer l’application
actuelle, chaque parcours Viewer, Admin, public et extension actuellement
disponible dans le dépôt de référence doit avoir un parcours équivalent dans la
V2, avec les mêmes règles métier effectivement approuvées. La refonte visuelle
du dashboard peut modifier la présentation et l’organisation des écrans, mais
ne doit pas retirer une action, une donnée, une restriction, un état ou une
capacité disponible.

La parité ne se déduit pas uniquement du nom d’une page ou d’une route. Pour
chaque capacité, l’inventaire V2 doit relier :

1. la route ou le point d’entrée actuel ;
2. le comportement observé dans le code et ses tests ;
3. la règle métier dans les documents canoniques ;
4. le comportement attendu dans la V2 ;
5. un critère d’acceptation vérifiable.

En cas de divergence entre le code, les tests et la documentation, la V2 ne
choisit pas silencieusement une version. La divergence est inscrite dans le
registre des décisions ci-dessous et la règle est confirmée avant
l’implémentation de la capacité concernée.

## 4. Ce qui est conservé et ce qui est reconstruit

| Partie | Traitement V2 | Référence dans le dépôt actuel | Règle de reprise |
| --- | --- | --- | --- |
| Vitrine publique | Conservée avec une fidélité visuelle stricte à la V1 | `frontend/src/app/page.tsx`, layouts, composants réellement importés et styles de la vitrine | Reprendre la chaîne d’implémentation nécessaire à son rendu sans la redessiner. Seuls les branchements techniques invisibles (API, routage, chemins d’assets) peuvent changer. Tout écart visible exige l’approbation explicite du propriétaire avant implémentation. |
| Connexion et Inscription | Rendu et parcours visibles 100 % identiques à la V1; appels réimplémentables | `frontend/src/app/connexion/`, `frontend/src/app/inscription/`, composants et styles importés | Garder les mêmes champs, textes, validations, erreurs, liens, langues, proportions, disposition et interactions visibles. Les appels peuvent cibler l’API V2 si aucun rendu ou parcours visible ne change. Tout écart exige une approbation préalable. |
| Images | Seules les images réellement utilisées sont conservées et récupérées depuis le dépôt Git de référence | Dépôt `Krapaud-Labs/Skkup`, branche `dev`, au commit de référence fixé dans ce cahier; chemins d’assets et usages inventoriés depuis ce snapshot | Extraire les fichiers depuis le commit de référence, puis les copier sans retouche. Générer avant copie un manifeste chemin source, usages, empreinte SHA-256 et chemin V2. Le checkout local ou la seule présence d’un fichier dans un dossier ne suffit pas à le garder. Exclure les doublons inutilisés, maquettes et anciens médias. |
| Frontend de l’extension | Interface actuelle conservée | `extension/src/popup/` et composants/styles directement utilisés par le popup | Préserver les écrans, textes, états visuels, saisie du code d’appairage et affichage de progression. Toute adaptation nécessaire à l’API Python doit être isolée et tracée. |
| Dashboard Viewer | Reconstruit de zéro | Routes actuelles sous `frontend/src/app/dashboard/` et composants sous `frontend/src/components/dashboard/` | Reprendre toutes les fonctions et règles, sans copier l’organisation ou les composants du dashboard actuel. |
| Dashboard Admin | Reconstruit de zéro | Routes sous `frontend/src/app/admin/` et composants sous `frontend/src/components/admin/` | Reprendre chaque capacité Admin réelle, y compris les contrôles d’accès, validations, statuts et historiques. |
| Backend | Réécrit en Python/FastAPI | `backend/src/`, `backend/prisma/schema.prisma`, `docs/04-api-contract.md` | Réimplémenter les capacités et contrats nécessaires. Aucune logique métier ne doit rester dépendante du backend NestJS/Prisma. |
| Modèle et migrations | Recréés avec SQLAlchemy et Alembic | `backend/prisma/schema.prisma`, migrations Prisma, `docs/03-data-model.md` | Traduire les contraintes d’intégrité, transactions, unicités et index utiles. Prisma n’est pas une dépendance V2. |
| Extension hors interface | À reconstruire ou adapter selon le besoin | `extension/src/arriere-plan/`, `extension/src/contenu/`, `extension/src/commun/`, `extension/src/manifeste.ts` | L’accord porte explicitement sur le frontend de l’extension. Le manifeste, le worker, les scripts de contenu et la logique de mesure ne sont pas déclarés conservés tels quels. Leur équivalence fonctionnelle demeure obligatoire. |
| Docker et exploitation | Recréés pour la nouvelle stack | `docker-compose*.yml`, `backend/Dockerfile*`, `frontend/Dockerfile`, `docs/08-docker-infra.md` | Conserver les capacités nécessaires, pas les anciens conteneurs ou commandes par simple copie. |

### 4.1 Manifeste des actifs conservés

Avant la première copie de code ou d’image, établir dans le nouveau dépôt un
manifeste versionné qui indique pour chaque actif retenu : dépôt, branche et
commit source, chemin V1, chemin V2, SHA-256, composant qui le référence, usage
observé, format/dimensions et provenance/licence connue. Les images retenues
doivent être extraites du snapshot Git de référence décrit au §1, puis copiées
à l’identique; les fichiers seulement présents dans un checkout local ne sont
pas une source de remplacement. Inclure les images référencées dans les
métadonnées SEO, CSS, composants, vitrines, popup et captures intégrées au
produit si elles sont réellement utilisées. Ne pas copier les répertoires
d’assets en bloc.

Les chemins actuellement repérés dans le dépôt de référence comprennent notamment
`frontend/assets/marketing/hero/skkup-hero-products.png`, les images de la
vitrine dans `frontend/assets/marketing/steps/`, le fond
`frontend/public/assets/marketing/backgrounds/vitrine-neon-brick.webp` et les
logos référencés par les métadonnées et composants. Cette liste est indicative,
pas l’inventaire définitif : le manifeste doit être construit depuis les usages
au moment de la reprise.

### 4.1.1 Fidélité obligatoire de la vitrine et des pages d’authentification

La consigne « comme deux gouttes d’eau » signifie que la vitrine V2 et les pages
Connexion/Inscription doivent présenter le même rendu que la V1, et non
simplement reprendre son thème. À contenu, langue, état des données, viewport et
environnement de rendu identiques, doivent rester identiques : structure et
ordre des sections, libellés, textes, champs, liens, images, recadrages, tailles,
positions, marges, espacements, couleurs, typographies, fonds, effets,
animations, points de rupture responsive, interactions, destinations des liens
et comportement de scroll.

- Conserver la source actuelle de la vitrine et ses styles autant que possible;
  ne pas la reconstruire à partir de captures ou maquettes si sa source est
  réutilisable. Les pages Connexion et Inscription peuvent être réimplémentées
  en React/TypeScript, mais doivent reproduire exactement leur référence V1.
- Ne pas modifier le contenu, l’ordre, la composition, l’échelle, les couleurs,
  les effets, les animations ou la navigation sous prétexte de modernisation,
  simplification, cohérence avec le nouveau dashboard ou adaptation à React.
- Les seules modifications permises sans décision visuelle sont les changements
  techniques indispensables d’intégration : endpoint API, routage interne,
  mécanisme de chargement ou chemin d’asset. Ils ne doivent changer ni les
  pixels visibles, ni le contenu, ni l’interaction observable.
- Toute différence visible par rapport à la V1, même mineure et même présentée
  comme nécessaire, doit être documentée et approuvée explicitement par le
  propriétaire avant son implémentation. Sans cette approbation, elle doit être
  corrigée pour retrouver la référence V1.
- Préserver les métadonnées SEO, sociales, icônes, données structurées, langues
  et indexation de la vitrine. Une valeur d’URL liée au nouveau domaine peut
  différer si le contenu reste identique.

### 4.2 Frontend de l’extension conservé

Le périmètre conservé vise l’interface popup de l’extension et ses éléments
nécessaires à l’affichage du code d’appairage et de la progression, notamment
les fichiers actuellement sous `extension/src/popup/`. Les scripts de suivi, le
worker, les permissions, le manifeste de publication et le contrat avec le
backend devront être inventoriés séparément. Aucune permission navigateur
supplémentaire ne sera ajoutée sans exigence fonctionnelle justifiée.

## 5. Fonctionnalités à préserver

Les éléments ci-dessous constituent le périmètre de parité attendu. Les règles
marquées comme non décidées restent des questions ouvertes : le fait qu’une
fonction existe dans le code ne constitue pas à lui seul une décision de
politique produit.

### 5.1 Vitrine et pages publiques

- Conserver la vitrine existante, son contenu, ses sections, ses images
  effectivement utilisées, son comportement de navigation/scroll et ses
  métadonnées de référencement avec un rendu visuel identique à la V1. La
  conformité se juge par comparaison directe avec la V1, pas par proximité du
  thème.
- Reproduire les mêmes compositions aux largeurs de référence 320, 390, 768,
  1024, 1280, 1440 et 1920 pixels, en FR et EN, avec un état de données
  équivalent. Les sections, leur ordre et leurs points de rupture correspondent
  à la référence.
- Comparer les captures V1/V2 en superposition et par image-diff dans le même
  navigateur, version, zoom, densité de pixels, langue, état applicatif et
  viewport. Masquer uniquement les zones dynamiques préalablement inventoriées;
  comparer séparément leur présence, dimensions et style. Aucun autre masque
  n’est permis.
- Critère de réussite : **zéro différence visuelle non approuvée**. Tout écart
  signalé par l’image-diff doit être corrigé ou approuvé explicitement par le
  propriétaire; aucun seuil de similarité arbitraire ne vaut approbation.
- Vérifier les liens, boutons, ancres, sélecteur de langue, navigation clavier,
  bouton retour et scroll contre la V1; destinations et résultats observables
  restent identiques.
- Isoler les styles du nouveau dashboard pour qu’ils ne modifient ni la
  vitrine ni les pages d’authentification.
- Maintenir l’accès public aux informations prévues : accueil, présentation,
  FAQ, règlement, confidentialité, contenus éditoriaux publiés, annonces,
  tirages publics et résultats vérifiables.
- Maintenir l’affichage des partenaires et des lots à partir des données réelles.
- Ne pas remplacer une image indisponible par une image inventée.
- Préserver les versions linguistiques actuellement exposées (FR/EN) et le
  sélecteur de langue. Inventorier le contenu non traduit avant de déclarer la
  parité complète.

Références : `frontend/src/app/page.tsx`, `frontend/src/app/layout.tsx`,
`frontend/src/app/faq/`, `frontend/src/app/reglement/`,
`frontend/src/app/confidentialite/`, `frontend/src/app/extension/`,
`docs/seo.md`, `docs/internationalisation.md`.

### 5.2 Comptes, sessions et profil

- Pages Connexion et Inscription : même rendu visuel et mêmes interactions
  visibles que la V1, dans les états initial, chargement, validation et erreur.
  Les appels d’authentification peuvent être réimplémentés pour l’API V2; aucun
  changement de présentation ou résultat visible n’est permis.
- Reproduire les mêmes champs, contraintes, textes, erreurs, liens et focus.
  Connexion conserve les champs email/mot de passe et la redirection après
  réussite. Inscription conserve pseudo, email, mot de passe et confirmation,
  indicateurs de règles et messages de non-correspondance.
- Conserver le parcours d’acceptation du règlement avant l’inscription, y
  compris contenu, modal, scroll, case à cocher, boutons et fermeture.
- Comparer chaque page à 1440×900 et 390×844, en FR et EN, à l’état initial et
  après soumission invalide reproductible. Le diff est nul dans les zones
  statiques; toute différence visible non approuvée échoue au critère 100 %.
- Tester les erreurs sans compte réel ni inscription effective, au moyen de
  réponses API synthétiques isolées.
- Inscription native avec adresse email, mot de passe, pseudo et acceptation
  explicite du règlement.
- Connexion et déconnexion; la déconnexion révoque au minimum la session
  courante, selon le contrat actuel.
- Changement de mot de passe avec révocation des sessions et de l’appareil
  d’extension associé, si ce comportement reste celui de la référence active.
- Espaces Viewer et Admin séparés par autorisation côté serveur.
- Profil, préférences de langue et données de compte exposés par les parcours
  actuels.
- Aucun fournisseur OAuth tiers n’est une méthode de création ou de connexion
  Skkup dans le cahier V1 accepté.

La récupération de mot de passe, la vérification d’email, la modification du
pseudo/email et la suppression/export des données doivent être comparées au
comportement réel et arbitrées avant la parité finale; les documents actuels ne
suffisent pas à certifier tous ces parcours.

Références : `frontend/src/app/connexion/`, `frontend/src/app/inscription/`,
`frontend/src/app/dashboard/compte/`, `backend/src/auth/`,
`backend/src/me/`, `docs/04-api-contract.md`, `docs/05-security.md`.

### 5.3 Visite quotidienne, points, progression et streak

- Créditer la visite quotidienne conformément à la règle effective de la
  référence, avec protection contre les crédits répétés le même jour.
- Afficher le solde courant, sa progression et l’historique des opérations.
- Afficher le streak courant et maximal, le prochain palier et les gains déjà
  obtenus.
- Reprendre les paliers documentés de 1, 3, 7, 14 et 30 jours : un palier ne
  paie qu’une seule fois, un jour manqué réinitialise le compteur et les gains
  antérieurement acquis restent conservés.
- Garder le backend comme source de vérité du solde et du temps crédité.
- Afficher les événements d’activité récents dans les dashboards concernés.

Les montants du check-in quotidien et les récompenses exactes des paliers sont
à extraire du code/tests actuels et à confirmer si les sources se contredisent.
Ils ne sont pas inventés dans ce cahier.

Références : `backend/src/me/`, `backend/src/watch-sessions/`,
`backend/src/scratch-cards/`, `frontend/src/components/dashboard/`,
`docs/01-features.md` §2–3, `docs/product/user-stories.md`.

### 5.4 Visionnage et attribution de points

- Mesurer le temps via la chaîne d’extension existante, et non par la seule
  ouverture d’une page Skkup.
- Réutiliser les plateformes de visionnage réellement supportées par la
  référence; les documents nomment Twitch, YouTube et Kick et excluent Facebook.
- Suspendre le suivi lorsque le visionnage n’est pas actif selon les règles
  effectives de l’extension (par exemple onglet en arrière-plan, lecteur en
  pause ou session invalide).
- Envoyer des heartbeats authentifiés; recalculer et valider les durées côté
  serveur, empêcher rejeu, double crédit, concurrence et dépassement des
  plafonds.
- Appliquer le barème, les éventuels bonus partenaire et le plafond quotidien
  tels qu’ils sont confirmés avant implémentation.
- L’extension affiche le statut de connexion, le compte associé, la progression
  XP/points, la progression jusqu’au prochain palier, les états d’erreur et les
  informations de session actuellement disponibles.
- La barre de progression doit refléter les crédits acceptés par le backend,
  sans afficher une progression locale comme un crédit garanti. Elle se met à
  jour au prochain événement temps réel ou rafraîchissement prévu, avec état de
  synchronisation compréhensible.

**Conflit à résoudre :** `docs/01-features.md` expose les valeurs horaires
1 h=10, 2 h=20, 3 h=35, 4 h=45, 5 h=55, 6 h=65, 7 h=75 et 8 h=90, alors que la
story `US-004` indique un plafond de 65 points. Les commentaires de code, les
tests et le comportement de la branche de référence doivent être comparés; le
propriétaire valide ensuite une règle unique. La table ne doit pas être
recopiée comme règle V2 tant que ce conflit n’est pas résolu.

La matrice exacte navigateur/OS est également à vérifier. Les documents V1
limitent l’éligibilité à l’extension Chrome sur ordinateur, tandis que certains
fichiers décrivent une base WebExtension destinée à plusieurs navigateurs.

Références : `extension/src/`, `backend/src/watch-sessions/`,
`backend/src/streams/`, `backend/src/extension/`,
`docs/01-features.md` §3, `docs/02-architecture.md` « Extension navigateur »,
`docs/04-api-contract.md` « Visionnage » et « Extension navigateur ».

### 5.5 Appairage et révocation de l’extension

- Générer depuis le compte un code d’appairage à usage unique; il expire après
  cinq minutes et sa génération invalide le code précédent non consommé.
- Autoriser au plus un appareil associé actif par compte.
- Refuser un deuxième appairage actif sans consommer un code valide.
- Permettre la révocation depuis le site; un jeton révoqué doit être refusé
  immédiatement côté backend.
- Le jeton d’extension est distinct du cookie web, opaque, révocable et ne
  donne accès qu’aux fonctions nécessaires au visionnage.
- N’afficher aucune liste d’appareils historiques si elle n’est pas présente
  dans le parcours actuel; les détails d’appareil non nécessaires ne sont pas
  collectés.

Références : `frontend/src/app/dashboard/extension/`,
`extension/src/popup/code-appariement.ts`, `backend/src/extension/`,
`docs/04-api-contract.md` « Génération du code d’appariement »,
« Gestion des appareils appariés » et `docs/05-security.md` §469.

### 5.6 Cartes à gratter et récompenses Viewer

- Reprendre les catégories, disponibilités, états non utilisés/utilisés,
  conditions de déblocage, animation/révélation, gains et historique qui sont
  effectivement actifs dans la référence.
- Afficher les récompenses possédées et les états disponibles selon le compte.
- Protéger l’action de grattage contre les appels répétés et les doubles gains.
- Conserver les médias de carte réellement référencés par le parcours retenu.

Les valeurs, probabilités et règles exactes de distribution ne sont pas
uniformément établies par les documents. Elles doivent être comparées à
`backend/src/scratch-cards/`, aux fixtures et aux tests avant d’être fixées
comme critères V2. Ne jamais inventer une probabilité à partir du visuel ou du
nom d’un palier.

Références : `frontend/src/app/dashboard/recompenses/`,
`backend/src/scratch-cards/`, `frontend/assets/dashboard/rewards/`,
`docs/design/scratch-card-mockups/README.md`, `docs/04-api-contract.md`
« Cartes à gratter ».

### 5.7 Tirages, lots, tickets et gagnants

- Publier les tirages ouverts et passés, les lots, dates, conditions et
  quantités/tickets publiques prévues.
- Permettre à l’Admin de créer/modifier un tirage tant qu’il est modifiable,
  gérer ses lots et sponsors, ouvrir/clôturer et déclencher manuellement le
  tirage selon le rôle autorisé.
- Une fois publié ou clôturé, protéger l’immuabilité des informations
  nécessaires à la vérification.
- Rendre le tirage vérifiable : liste des tickets figée, graine, empreinte,
  algorithme documenté, horodatage et résultat consultable après le tirage.
- Afficher les gagnants par pseudo et identifiant de ticket, sans divulguer
  email ou identifiant interne; respecter le consentement requis pour publier
  un pseudo.
- Préserver l’historique des tirages et des lots.
- Conserver les tickets obtenus par les sources actuellement actives et
  relier chaque ticket à son utilisateur et au tirage concerné.
- Conserver la boutique de tickets : achat en points d’un ticket associé à un
  tirage ouvert, si cette capacité demeure activée après la revue juridique
  applicable. Débit, commande et création du ticket doivent être atomiques.

Le cahier accepté décrivait le tirage manuel hebdomadaire et un tirage mensuel
différé. La V2 doit reprendre le calendrier actuellement utilisé, sans
réactiver un calendrier uniquement parce qu’il figure dans une ancienne
section V1.0/V1.1.

Références : `frontend/src/app/dashboard/tirages/`,
`frontend/src/app/admin/raffles/`, `backend/src/raffles/`,
`backend/src/sponsors/`, `backend/src/admin-lots/`,
`docs/01-features.md` §5 et §7, `docs/02-architecture.md` « Modèle de tirage
au sort », `docs/04-api-contract.md` « Tirages au sort »,
`docs/10-legal-compliance.md`.

### 5.8 Boutique Viewer et gestion Admin

- Présenter les articles actifs disponibles, leur type, coût en points, stock
  disponible et limite restante pour l’utilisateur.
- Permettre l’achat après confirmation, seulement si solde, stock, limite et
  statut du tirage lié le permettent.
- Rendre le débit de points, l’achat et l’attribution du code/ticket
  atomiques, sérialisés face aux achats concurrents et idempotents.
- Afficher l’historique personnel « Mes achats » sans exposer les codes dans
  les listes; révéler un code numérique uniquement à son acheteur.
- Dans l’Admin, créer/modifier/désactiver les articles, fixer le prix en points,
  les stocks/limites et le tirage lié; importer les codes sans les afficher en
  clair dans la réponse ou les journaux.
- Préserver les types actuellement décidés : codes promotionnels, bons d’achat
  numériques et tickets de tirage.
- Ne pas introduire de paiement en argent, achat de points, conversion monétaire
  ni retrait d’argent.
- La livraison de codes reste consultable dans Mes achats; aucun envoi email
  n’est promis tant qu’un service d’email n’est pas configuré.

Références : `frontend/src/app/dashboard/boutique/`,
`frontend/src/app/admin/shop/`, `backend/src/shop/`,
`docs/01-features.md` §4, `docs/04-api-contract.md` « Boutique ».

### 5.9 Administration générale

Reprendre les opérations réelles des pages et API Admin actuelles :

- Cockpit et synthèse des indicateurs, avec données persistées et bornes
  adaptées au volume.
- Gestion des tirages, lots et sponsors.
- Gestion du catalogue de la boutique et suivi des commandes sans révélation
  des codes privés.
- Gestion des utilisateurs et changements d’état autorisés.
- Gestion des annonces : brouillon, publication explicite, désactivation ou
  archivage/restauration selon le cycle actuellement implémenté.
- Gestion des contenus éditoriaux versionnés, prévisualisation et publication.
- Consultation et traitement des signalements antifraude, avec séparation
  entre le signalement et l’état du compte.
- Journal d’audit des opérations Admin, avec acteur, action, cible, date,
  résultat et contexte minimal nécessaire.
- Refus serveur de toute opération Admin à un compte non administrateur,
  même si l’interface masque le bouton ou la page.

#### Création Admin exclusivement par modale

Toute création déclenchée depuis l’administration s’effectue **uniquement dans
une boîte de dialogue modale**, sur la route Admin courante. Cette règle couvre
toute entité que l’Admin peut créer, notamment annonce, tirage/loterie, lot,
sponsor, contenu éditorial et article de boutique, ainsi que toute nouvelle
entité ajoutée ultérieurement.

- Aucun formulaire de création inline, panneau latéral non modal ou route/page
  dédiée de création n’est autorisé.
- La modale reste une modale sur mobile. Elle peut occuper presque tout ou tout
  l’écran, avec son propre défilement, mais ne devient pas une page autonome.
- Chaque modale a un titre accessible, un focus placé à l’ouverture, un focus
  contenu dans la boîte tant qu’elle est ouverte, des libellés explicites et
  des erreurs reliées aux champs concernés. Le clavier peut parcourir tous les
  champs et actions; la fermeture rend le focus au bouton déclencheur.
- Les actions Annuler et Échap abandonnent la création sans rien enregistrer.
  Si des champs ont été modifiés, demander confirmation avant de les perdre.
- Une erreur de validation empêche l’enregistrement et affiche les erreurs
  près des champs. Une erreur serveur laisse la modale ouverte, conserve les
  valeurs saisies et permet une nouvelle tentative.
- Pendant l’envoi, afficher l’état de traitement et empêcher les doubles
  soumissions. Au succès, fermer la modale, confirmer l’action et actualiser la
  liste sans créer de doublon.
- Cette exigence concerne les **créations seulement**. Elle ne transforme pas
  automatiquement les parcours d’édition actuels en modales.
- Toute autre présentation de création exige l’accord explicite préalable du
  propriétaire.

Les routes et listes Admin servent de contexte : le bouton « Créer » ouvre la
modale sans navigation et la liste conserve son état au retour.

Références : routes sous `frontend/src/app/admin/`,
`backend/src/admin-dashboard/`, `backend/src/admin-users/`,
`backend/src/announcements/`, `backend/src/content/`,
`backend/src/fraud-flags/`, `backend/src/raffles/`,
`backend/src/sponsors/`, `backend/src/shop/`,
`docs/04-api-contract.md` « Administration ».

### 5.10 Annonces et contenu éditorial

- Les annonces administrées ont un cycle contrôlé, des dates optionnelles,
  publication distincte de l’édition et archivage sans effacer l’historique.
- Les viewers voient uniquement les annonces publiées conformément au
  comportement documenté; leur état de lecture reste local au profil/navigateur
  si c’est toujours le comportement de la référence.
- Les contenus éditoriaux disposent d’un historique de versions; seuls les
  contenus publiés sont servis publiquement.
- Les données libres sont rendues de façon sûre et ne permettent pas
  l’injection de scripts ou de styles actifs.

Références : `frontend/src/app/admin/announcements/`,
`backend/src/announcements/`, `backend/src/content/`,
`docs/design/announcement-lifecycle-2026-10-22.md`,
`docs/04-api-contract.md` « Administration ».

### 5.11 Temps réel

- Maintenir l’actualisation du solde et de ses événements, du streak, des
  cartes débloquées, de l’état d’appairage et des résultats/statuts de tirage
  lorsque la source actuelle émet ces événements.
- Toute donnée importante reste relisible par REST après déconnexion,
  reconnexion ou perte d’événement; le WebSocket n’est jamais l’unique source
  de vérité.
- Les rooms/abonnements privés sont décidés côté serveur; aucun client ne peut
  choisir l’identifiant d’un autre utilisateur.

La compatibilité Socket.IO du dashboard actuel, le WebSocket natif FastAPI et
la nécessité éventuelle d’un adaptateur sont des choix techniques ouverts.

Références : `backend/src/realtime/`, `docs/02-architecture.md` « Temps réel
WebSocket », `docs/04-api-contract.md` « Temps réel ».

## 6. Architecture technique cible

### 6.1 Stack décidée

- **API/backend :** Python avec FastAPI.
- **Validation et schémas API :** Pydantic, demandé par le propriétaire.
- **Accès aux données :** SQLAlchemy.
- **Base :** PostgreSQL.
- **Interface :** React avec TypeScript.
- **Exécution :** Docker.

### 6.2 Bibliothèques et outils recommandés, à confirmer au démarrage V2

Cette baseline vise une architecture lisible, testable et peu couplée. Les
versions exactes ne sont pas figées dans ce cahier : elles seront choisies au
démarrage du nouveau dépôt parmi les versions stables compatibles, puis
verrouillées dans les fichiers de dépendances. Ces recommandations n’ajoutent
aucun service payant ni fournisseur SaaS obligatoire.

| Domaine | Baseline recommandée | Règle d’architecture |
| --- | --- | --- |
| API et validation | FastAPI, Pydantic 2 et `pydantic-settings` | Définir des modèles Pydantic distincts pour les entrées/sorties HTTP et la configuration. Valider la configuration au démarrage. Garder les modèles API séparés des entités SQLAlchemy; la validation métier et de sécurité faisant autorité reste côté serveur. |
| Accès PostgreSQL et migrations | SQLAlchemy 2, Alembic et un pilote PostgreSQL maintenu, recommandé Psycopg 3 | Versionner les migrations, les relire et les tester contre PostgreSQL réel. Ne pas créer ou modifier le schéma automatiquement au démarrage en production. |
| Dépendances Python | `uv` avec `pyproject.toml` et `uv.lock` | Reproduire installations locale et CI depuis le lockfile; fixer la version Python au premier démarrage selon la compatibilité du stack retenu. |
| Qualité et types Python | Ruff pour lint/format, mypy pour le contrôle statique | Configuration commune locale/CI, vérification incrémentale des types et aucune désactivation générale des erreurs. |
| Tests backend | pytest et HTTPX/TestClient | Tests unitaires des règles métier, API et permissions; tests d’intégration sur PostgreSQL en conteneur pour vérifier transactions, contraintes et concurrence. SQLite ne remplace pas ces tests PostgreSQL. |
| Contrat API vers TypeScript | Schéma OpenAPI FastAPI et génération de types/client TypeScript, recommandation `openapi-typescript` avec `openapi-fetch` | Générer les artefacts depuis l’API; vérifier en CI qu’ils sont à jour. Ne pas maintenir à la main une seconde définition du contrat. |
| Données côté React | TanStack Query | Réserver cette couche à l’état serveur (lecture, cache, mutations et invalidation). Ne pas ajouter de magasin global tant qu’un besoin d’état client partagé n’est pas démontré. |
| Formulaires React | React Hook Form et Zod | Partager les erreurs et les validations d’interface, y compris dans les modales Admin. Le client améliore l’expérience, mais ne remplace jamais la validation Pydantic et les règles métier du backend. |
| Tests frontend | Vitest et React Testing Library | Couvrir composants et comportements unitaires sans dépendre de leurs détails d’implémentation. |
| Parcours navigateur | Playwright | Réserver les scénarios E2E aux parcours critiques, à la validation finale des cartes et à la comparaison V1/V2; ne pas exécuter la suite navigateur après chaque changement mineur. |
| Conteneurs | Docker et Docker Compose | Définir des services séparés, des healthchecks et une commande de migration contrôlée. Les tests d’intégration démarrent une base PostgreSQL isolée. |
| Observabilité | Logs structurés avec filtrage des données sensibles; OpenTelemetry si une destination compatible est retenue | Prévoir les points d’instrumentation sans imposer de plateforme payante. Ne jamais envoyer secrets, codes privés ou données personnelles superflues dans les logs/traces. |
| CI et dépendances | GitHub Actions, lockfiles obligatoires, contrôles lint/types/tests/build et analyse des dépendances | Rendre les contrôles reproductibles et bloquants selon la gravité; documenter les exceptions avec une échéance. Les versions et actions sont fixées par SHA ou contrainte de version au démarrage. |

La génération OpenAPI/TypeScript assure la cohérence structurelle des contrats,
mais ne partage pas les règles métier du serveur. Les schémas Zod servent à
afficher tôt les erreurs de formulaire; Pydantic et le backend restent seuls
responsables d’accepter ou refuser une opération.

**Sources officielles consultées le 2026-11-14 :** [FastAPI, validation et
OpenAPI](https://fastapi.tiangolo.com/features/), [Pydantic, modèles](https://docs.pydantic.dev/latest/concepts/models/)
et [configuration](https://docs.pydantic.dev/latest/concepts/pydantic_settings/),
[SQLAlchemy 2](https://docs.sqlalchemy.org/en/20/orm/quickstart.html),
[Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html),
[Psycopg 3](https://www.psycopg.org/psycopg3/docs/),
[uv](https://docs.astral.sh/uv/concepts/projects/), [Ruff](https://docs.astral.sh/ruff/),
[mypy](https://mypy.readthedocs.io/en/stable/), [pytest](https://docs.pytest.org/en/stable/),
[tests FastAPI](https://fastapi.tiangolo.com/tutorial/testing/),
[openapi-typescript](https://openapi-ts.dev/introduction),
[TanStack Query](https://tanstack.com/query/latest/docs/framework/react/overview),
[React Hook Form](https://react-hook-form.com/get-started), [Zod](https://zod.dev/),
[Vitest](https://vitest.dev/guide/), [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/),
[Playwright](https://playwright.dev/docs/intro), [Docker Compose](https://docs.docker.com/compose/)
et [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/).

### 6.3 Baseline d’architecture recommandée, à confirmer

- Monolithe modulaire côté API plutôt que microservices.
- Modules métier à frontières claires : auth/session, profil, points/check-in,
  watch sessions, extension, streak/récompenses, cartes à gratter, boutique,
  tirages/lots/sponsors, annonces/contenus, administration, antifraude et
  temps réel.
- SQLAlchemy 2 et Alembic pour le mapping et toutes les migrations versionnées.
- PostgreSQL seule source de vérité des soldes, tickets, commandes, codes,
  tirages, résultats, sessions et droits.
- API REST JSON documentée OpenAPI. Maintenir en priorité les chemins et
  payloads consommés par l’extension dont le frontend est conservé; ajouter un
  adaptateur versionné si un changement est indispensable.
- Isoler les règles métier des contrôleurs HTTP et des composants React.
- Docker Compose local avec services séparés pour interface, API et PostgreSQL;
  service worker et Redis seulement si leur besoin fonctionnel est confirmé.
- Configurations par environnement, secrets injectés à l’exécution, migrations
  lancées comme étape contrôlée, healthchecks et logs structurés sans secrets.
- Les entités SQLAlchemy, schémas Pydantic et types TypeScript générés restent
  séparés; les frontières et conversions entre ces modèles sont explicites.

**Framework frontend à confirmer :** React/TypeScript est décidé, mais Vite
versus Next.js n’est pas. La recommandation est de garder Next.js pour préserver
le code de vitrine et son rendu/SEO, puis de reconstruire entièrement les routes
dashboard en React/TypeScript dans cette application. Une SPA Vite séparée
nécessiterait une décision explicite sur la reprise des métadonnées SEO, le
routage et le partage visuel de la vitrine.

**Tâches asynchrones à confirmer :** les agrégations, expirations, notifications
et tirages planifiés peuvent nécessiter un worker Python. Redis et Celery (ou
un choix plus léger) ne sont pas décidés par le propriétaire. Aucun composant
supplémentaire n’est ajouté sans cas d’usage documenté. Les opérations
transactionnelles restent dans PostgreSQL.

## 7. Exigences de sécurité et d’intégrité

- Mots de passe hachés avec un algorithme adapté et paramètres maintenables.
- Session web en cookie `HttpOnly`, `Secure` en production, politique `SameSite`
  définie et protections CSRF/origin pour les mutations.
- Jeton extension distinct de la session web, à haute entropie, stocké sous
  forme hachée et révocable; code d’appairage à usage unique, courte durée,
  limitations de débit et réponse non-oracle.
- Un seul appareil d’extension actif par compte; unicité garantie aussi par la
  base, pas uniquement par le code Python.
- Contrôle de rôle Admin à chaque endpoint; jamais uniquement dans React.
- Validation de toutes les entrées, limites de taille/pagination, rate limiting
  des routes sensibles et configuration CORS stricte.
- Vérifier `Origin`, les proxys de confiance et les adresses forwarded selon
  les hôtes/proxys réellement déployés.
- Prévenir double crédit, double grattage, double achat, rejeu de heartbeat,
  course sur le stock et double tirage au moyen de transactions, contraintes,
  verrouillages ou clés idempotentes adaptées.
- Chiffrer les codes numériques au repos avec une clé hors dépôt, versionnée et
  rotatable. Ne jamais révéler codes, jetons, mots de passe ou clés dans les
  logs, dumps, réponses Admin ou traces CI.
- Limiter les données personnelles collectées et définir suppression,
  exportation, rétention et anonymisation avant l’activation publique.
- Ne pas présenter la détection de présence de l’extension comme une mesure
  officielle fournie par Twitch, YouTube ou Kick.
- Exécuter des tests négatifs Admin, d’isolation entre comptes, d’expiration/
  révocation de jetons et de concurrence sur points/tickets/achats.

Références : `docs/05-security.md`, `backend/src/auth/`,
`backend/src/extension/`, `backend/src/watch-sessions/`, `backend/src/shop/`.

## 8. Données et migration

L’objectif de migration de données n’est pas décidé. Comme le propriétaire
indique qu’il n’y a pas d’usage actif, la baseline recommandée est une base V2
neuve et un nouveau jeu de secrets, sans migration automatique de comptes,
soldes, tickets, cartes à gratter, commandes ou sessions de production.

Avant cette décision finale :

1. inventorier en lecture seule si la production contient des comptes, soldes,
   résultats, commandes, codes ou contenus qu’il faut conserver;
2. dresser la liste des données de démonstration, seed, configuration et
   contenus éditoriaux à reprendre manuellement;
3. obtenir confirmation du propriétaire sur la conservation ou suppression des
   données historiques;
4. ne jamais exporter un secret ou une donnée personnelle dans Git, une fixture
   de test ou un artefact partagé.

Si une reprise est demandée, concevoir séparément le mapping du schéma Prisma
réel vers SQLAlchemy, contrôler les sommes de soldes contre le ledger, vérifier
les liens tickets/tirages/achats, tester sur une copie anonymisée et documenter
sauvegarde, répétabilité et retour arrière. Une migration n’est pas implicite.

Références : `backend/prisma/schema.prisma`,
`backend/prisma/migrations/`, `docs/03-data-model.md`.

## 9. Qualité, livraison et critères d’acceptation

La V2 ne remplace pas la production tant que les critères applicables ne sont
pas tous satisfaits :

- Une matrice de parité route par route relie chaque page actuelle, action,
  statut, contrôle d’accès, règle métier et test V2.
- Les scénarios principaux couvrent création/connexion de compte, session,
  visite quotidienne, progression de streak, appairage et révocation,
  visionnage sur chaque plateforme cible, crédit exact des points, historique,
  cartes à gratter, boutique, achat concurrent, ticket, tirage auditable,
  annonces, contenu, utilisateurs et actions d’administration.
- Les tests backend couvrent services, endpoints, permissions, transactions,
  intégrité et cas négatifs; les tests de base testent réellement les
  contraintes PostgreSQL ciblées.
- Les tests frontend couvrent les parcours Viewer/Admin et états de chargement,
  vide, erreur, indisponibilité et accès refusé; tests responsive et clavier en
  passe finale de la carte de refonte.
- Pour chaque type d’entité créable depuis l’Admin, vérifier que l’action ouvre
  une modale sur la route courante et qu’aucune création inline, non modale ou
  sur une route dédiée n’existe. Couvrir ouverture, champs manquants, valeur
  invalide, annulation/Échap, confirmation de perte si formulaire modifié,
  erreur serveur avec conservation des valeurs, envoi sans double soumission et
  succès avec fermeture et liste actualisée. Vérifier clavier, focus/restauration
  du focus et présentation desktop/mobile. Vérifier séparément que cette règle
  n’impose pas de déplacer les formulaires d’édition existants.
- Les contrats OpenAPI, schéma de données et exemples sont versionnés et
  générés/vérifiés depuis le backend V2.
- L’extension conservée peut s’apparier et suivre un visionnage éligible avec
  la nouvelle API selon les plateformes décidées; son UI n’est pas réécrite.
- Les fichiers copiés de vitrine et les images sont reliés à leur manifeste
  avec SHA-256; la comparaison avant/après confirme qu’aucune modification
  visuelle involontaire n’a été introduite.
- Docker démarre l’environnement de développement avec une base vide, applique
  les migrations et fournit des healthchecks reproductibles.
- CI exécute lint, types, tests ciblés puis suite de livraison, build des images
  et contrôles de dépendances/sécurité retenus.
- Les dépendances Python et JavaScript sont verrouillées; la génération du
  contrat TypeScript depuis OpenAPI ne produit aucun diff lors de la CI. Les
  migrations et contraintes critiques passent sur une instance PostgreSQL
  éphémère dédiée aux tests.
- La documentation couvre installation, variables, migrations, seed non
  sensible, restauration, déploiement et rollback.
- Le domaine, certificats, secrets, base et variables de production ne sont
  pas modifiés avant une décision de mise en production.
- Captures de référence et tests de fidélité couvrent la vitrine et les pages
  Connexion/Inscription. Leur diff visuel est nul dans les zones statiques; un
  écart dynamique est documenté, masqué uniquement selon la liste approuvée et
  comparé séparément. Les erreurs d’authentification sont testées sans créer de
  compte réel.

## 10. Hors périmètre explicite de la V2 selon le cadrage actuel

- Réécriture ou refonte visuelle de la vitrine et des pages Connexion/
  Inscription. Une adaptation technique sans effet visible est permise; tout
  changement de rendu exige une approbation expresse préalable.
- Copie en bloc des anciens dashboards, composants Admin/Viewer ou du backend.
- Conservation automatique d’images simplement présentes dans le dépôt mais
  sans usage réel.
- Nouveau système d’identité OAuth de Twitch, YouTube, Google ou Facebook.
- Paiement en argent réel, achat de points, cash-out, ou récompenses physiques,
  sauf nouvelle décision expresse.
- Fonctionnalité commerciale non présente dans la référence (affiliation,
  offres partenaires rémunérées, abonnement payant).
- Suppression ou simplification de règles métier dans le seul but de réduire le
  périmètre technique.

## 11. Registre des décisions à confirmer avant l’implémentation

Ces questions forment une seule phase de cadrage. Les recommandations ci-dessous
sont des propositions, pas des décisions déjà prises.

| ID | Décision requise | Proposition recommandée | Pourquoi elle bloque le gel du cahier |
| --- | --- | --- | --- |
| D-01 | Nom, propriétaire et visibilité du nouveau dépôt | `Krapaud-Labs/Skkup-v2`, privé pendant la construction, public à décider | La création, les permissions et la publication du code sont des actions externes. |
| D-02 | Framework React | Garder Next.js/React/TS pour reprendre directement la vitrine et son SEO; refaire les routes dashboard en React/TS. Une autre solution doit prouver la même fidélité avant bascule. | Une SPA Vite change le rendu et le plan de conservation de la vitrine. |
| D-03 | Parité API de l’extension publiée | Garder d’abord les chemins/payloads actuellement consommés; toute évolution devient versionnée | Le frontend popup gardé ne doit pas perdre l’appairage ou la progression. |
| D-04 | Socket.IO ou WebSocket natif | Conserver une compatibilité avec le client existant, ou décider une mise à jour coordonnée; REST reste la récupération de secours | WebSocket natif FastAPI n’est pas protocolairement compatible avec Socket.IO. |
| D-05 | Worker et Redis | Ajouter Redis/worker Python seulement pour les jobs et le pub/sub effectivement nécessaires; confirmer Celery ou alternative | Cela détermine les conteneurs, les reprises de jobs et le déploiement. |
| D-06 | Politique de données | Base vide recommandée; confirmer s’il existe des contenus, paramètres, comptes Admin ou historiques à reprendre | « Pas utilisé » ne prouve pas qu’aucune donnée de valeur n’existe. |
| D-07 | Plafond et barème de points | Vérifier code/tests actuels et trancher le conflit 90 contre 65 avant d’écrire des tests V2 normatifs | Deux sources canoniques donnent des plafonds différents. |
| D-08 | Paliers, cartes et récompenses | Prendre les règles réellement actives comme baseline après extraction; faire confirmer tout montant/probabilité non documenté | Les valeurs de récompense ne peuvent pas être déduites des maquettes. |
| D-09 | Plateformes et navigateurs de l’extension | Conserver les plateformes actives réellement testées dans la version actuelle; confirmer la matrice de publication | La cible Chrome et la base multi-navigateurs sont décrites différemment selon les documents. |
| D-10 | Activité de la boutique de tickets | Garder le comportement actuel en développement; ne pas revendiquer la conformité juridique; décision d’activation publique après réexamen du règlement | L’échange points/tickets appelle une relecture du règlement et des conditions. |
| D-11 | Initialisation du premier Admin | Définir une procédure hors interface, auditée, protégée par configuration ponctuelle, puis désactivée | Aucun endpoint d’auto-promotion ne doit exister. |
| D-12 | Emails et récupération de compte | Garder les codes consultables dans Mes achats; ne promettre les emails qu’après choix/configuration d’un service | Aucun service de mailing n’est actuellement configuré. |
| D-13 | Outils exacts et versions du socle | Adopter la baseline de §6.2; figer versions stables compatibles, image Python, pilote PostgreSQL et éventuels remplacements au premier démarrage | Les versions disponibles évoluent; elles doivent être verrouillées ensemble et validées dans l’environnement Docker/CI cible. |

## 12. Références de travail

Les documents ci-dessous décrivent des intentions et contrats; le code et les
tests du commit de référence décrivent l’implémentation présente. Aucun
instantané de fichier ne dispense de relire la branche de référence avant la
copie ou le gel des contrats V2.

| Sujet | Référence actuelle |
| --- | --- |
| Cahier accepté V1 | `docs/project-management/cahier-des-charges/Skkup/PROJECT-BRIEF.md` |
| Fonctionnalités et limites métier | `docs/01-features.md` |
| Architecture et temps réel | `docs/02-architecture.md` |
| Modèle de données et relations | `docs/03-data-model.md`, `backend/prisma/schema.prisma` |
| Contrats HTTP, extension et Admin | `docs/04-api-contract.md` |
| Authentification, menaces, anti-fraude et données | `docs/05-security.md`, `docs/10-legal-compliance.md` |
| Infra Docker | `docs/08-docker-infra.md`, `docker-compose.yml`, `docker-compose.prod.yml` |
| Stories et incertitudes produit | `docs/product/user-stories.md`, `docs/product/user-flows.md` |
| Design et actifs | `docs/06-frontend-design-system.md`, `docs/design/media-inventory.md`, `frontend/assets/README.md` |
| Source de la vitrine | `frontend/src/app/page.tsx` et ses imports/usages effectifs |
| Source du popup de l’extension | `extension/src/popup/` et composants directement importés |
| Source des règles d’extension | `extension/src/`, `backend/src/extension/`, `backend/src/watch-sessions/` |

## 13. Décision de statut

Statut actuel : **reconstructed / à valider par le propriétaire**. Les
fonctionnalités et la stack sont cadrées à haut niveau par la conversation; le
nouveau dépôt, le framework React précis, les règles métier contradictoires, la
politique de données et le protocole temps réel ne sont pas encore gelés.

Ce document ne lance pas la construction technique. Après validation du cahier
et réponses aux décisions bloquantes, le projet V2 devra recevoir son profil,
son plan de conception, son architecture détaillée et ses critères de
livraison propres. Le dépôt Skkup actuel restera la référence historique et
fonctionnelle.
