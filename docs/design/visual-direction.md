# Direction visuelle et expérience

## Statut

Status: review

## Décisions acceptées

- **Vitrine et Connexion/Inscription :** conserver fidèlement le rendu et les interactions visibles de la V1. Toute différence nécessite une décision propriétaire préalable.
- **Popup de l'extension :** préserver son interface; seules les adaptations d'API sans effet visuel sont prévues.
- **Dashboard :** construire un shell Dashboard commun aux rôles Viewer et Admin, avec une navigation cohérente et des sections/actions affichées selon le rôle. Le backend reste l'autorité des permissions Admin; masquer une action dans l'interface ne remplace pas son contrôle serveur. Décision propriétaire du 2026-11-16, consignée au journal sous D-17.
- **Palette et langage visuel du Dashboard :** réutiliser l'identité V1 bleu nuit, violet et cyan, ses surfaces, dégradés et lumières sélectives. D-18 approuve cette famille visuelle; les détails d'écran et seuils responsive ci-dessous restent une baseline technique réversible.

## Baseline Dashboard réversible

La référence est `frontend/src/app/design-tokens.css` au commit V1 `Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`. Elle définit le fond `#07132d`, les surfaces `#0d2044` et `#122955`, les accents `#8b3dff` et `#16d9ff`, ainsi que les tokens géométriques/effets `--radius-card: 16px`, `--radius-control: 10px`, `--dashboard-content-gap: 1rem`, `--dashboard-panel-padding: clamp(1rem, 2vw, 1.5rem)` et `--shadow-glow-v3`. D-18 approuve la famille de palette et le langage visuel V1 pour Viewer et Admin; il n'approuve pas ces valeurs geometry/spacing ni leur transposition. Les valeurs V1 citées servent de références candidates; leur adoption dans V2 reste une baseline technique réversible.

### Shell et navigation

- **Desktop, plus de 900 px :** un rail de navigation persistant de 224 à 256 px et une zone de contenu flexible. Le rail peut défiler indépendamment; le contenu principal ne déborde pas horizontalement. Le titre de page et les actions courantes sont en tête du contenu.
- **900 px et moins :** reprendre le point de bascule V1 où le rail fixe devient une navigation de pleine largeur au-dessus du contenu. Baseline V2 proposée: garder les destinations de rôle visibles dans une bande compacte; sous 600 px, autoriser un menu pliable ou une rangée horizontale défilante, avec état ouvert/fermé annoncé et navigation clavier. Le choix exact entre menu et rangée reste réversible après le prototype.
- Afficher la section courante avec `aria-current="page"`, conserver un ordre de tabulation prévisible, et ramener le focus au bouton déclencheur quand un menu mobile est fermé. La navigation Viewer et Admin partage les mêmes composants et repères; ses liens/actions diffèrent selon le rôle. L'API refuse toute opération Admin non autorisée côté serveur.

### Viewer: ordre des sections de l'accueil

1. **En-tête:** salutation, titre « Tableau de bord » et accès aux actions de compte.
2. **Résumé:** solde de points, progression du streak et tickets disponibles; valeurs directement liées aux règles et à l'état retournés par l'API.
3. **À récupérer ou terminer:** cartes à gratter disponibles et tirage ouvert avec ses tickets/actions, en deux panneaux sur grand écran et l'un après l'autre sur mobile.
4. **Activité récente:** derniers mouvements du ledger, date et montant, avec un lien explicite vers l'historique complet.
5. **Extension et visionnage:** état d'appairage et progression de session, en panneau secondaire après le résumé; le détail complet reste dans la section Extension/Streams de la navigation.

Navigation Viewer proposée: Vue d'ensemble, Streams, Historique, Récompenses, Tirages, Extension et Compte. Aucun point, ticket ou statut d'appairage ne doit être déduit visuellement s'il n'est pas confirmé par l'API.

### Admin: ordre des sections de l'accueil

1. **En-tête:** titre « Administration » et actions d'administration courantes autorisées.
2. **File de priorité:** indicateurs de signalements, utilisateurs à examiner et tirages/opérations en attente; chaque indicateur ouvre la file correspondante.
3. **À traiter:** modération et utilisateurs signalés, en premier car ces items nécessitent une action explicite.
4. **Opérations:** tirages, lots et annonces/contenus à publier ou vérifier, en panneaux liés aux écrans de gestion dédiés.
5. **Traçabilité récente:** événements d'audit visibles aux seuls rôles autorisés, avec lien vers l'audit complet.

Navigation Admin proposée: Vue d'ensemble, Utilisateurs, Modération, Lots, Tirages, Annonces/Contenus, Boutique, Streams/Sponsors et Audit. Les panneaux d'accueil résument et dirigent vers les opérations complètes; ils ne remplacent pas leurs formulaires ou contrôles d'accès.

### Densité et espacement

- Utiliser un pas de base de 4 px et les espacements dominants 8, 16, 24 et 32 px. Garder 16 px entre panneaux sur petits écrans et 16 à 20 px sur desktop.
- Garder le padding des panneaux entre 16 et 24 px (`--dashboard-panel-padding`), un inset de contenu de 16 px, un rayon de panneau de 12 px (`--dashboard-radius-panel`) et le rayon de contrôle de 10 px. Le rayon de carte de 16 px s'applique aux grands conteneurs de carte, pas à tous les panneaux.
- Baseline réversible: à partir de 1181 px, conserver une grille Dashboard Viewer à deux zones et des KPIs Admin sur quatre colonnes si leur largeur le permet. De 801 à 1180 px, réduire les KPIs Admin à trois colonnes; à 800 px et moins, à deux, puis une colonne si le contenu est trop étroit. Les tables Admin deviennent des cartes lisibles ou un défilement horizontal explicite, sans masquer silencieusement des champs essentiels.

### Seuils responsives et comportement

Ces points de départ réutilisent les seuils observés dans `frontend/src/app/globals.css` V1, mais leur application V2 reste une décision d'implémentation réversible:

| Largeur | Baseline proposée | Référence V1 observée |
| ---: | --- | --- |
| 1181 px et plus | Rail latéral, KPIs Viewer en ligne, grilles Viewer/Admin multi-colonnes. | Shell latéral 224 à 256 px; grille de contenu Viewer en deux colonnes; KPIs Admin réduits à trois colonnes à 1180 px. |
| 901 à 1180 px | Rail conservé; KPI Admin en trois colonnes; panneaux secondaires gardent une largeur lisible. | Réduction des KPIs Admin à 1180 px. |
| 801 à 900 px | Navigation passe au-dessus; grilles Viewer en une colonne au seuil 850/900 px. | Shell en pleine largeur et rail statique à 900 px; grille Viewer en une colonne à 850 px. |
| 701 à 800 px | Panneaux Admin en une colonne; KPIs Admin en deux colonnes. | Grilles Admin en une colonne et KPIs en deux colonnes à 800 px. |
| 561 à 700 px | Tables Admin condensées sans perdre l'accès aux champs; actions de panneau peuvent passer sous le titre. | Tables Lots/Tirages et entêtes Admin compactés autour de 700 px. |
| 560 px et moins | Contenu en une colonne, nav pliable ou défilante; cartes scratch défilent sans réduire la cible d'action. | Cartes scratch d'au moins 12 rem; toolbar Viewer empilée à 560 px. |

Les largeurs de contrôle demandées restent 320, 390, 768, 1024, 1280, 1440 et 1920 px, en FR et EN. Cette table décrit une baseline, pas une preuve de rendu ni une approbation de chaque seuil.

### Etats, focus, clavier et lumière

- Chaque panneau utilise des états chargement, vide, erreur récupérable, succès et désactivé. Les erreurs annonçables utilisent `role="alert"`; chargements et mises à jour non urgentes utilisent un état `status`. Les actions de reprise sont explicites.
- Les liens et contrôles ont un focus clavier visible distinct du hover, avec un contour d'au moins 2 px et un décalage suffisant pour rester discernable sur les surfaces sombres. Les menus s'ouvrent et se ferment au clavier; Escape ferme un menu mobile; le focus ne se perd pas dans un panneau masqué.
- Maintenir les contrôles interactifs à au moins 44 px de hauteur. Mesurer les contrastes dans les deux rôles et langues selon WCAG 2.2: texte courant au moins 4.5:1; grand texte au moins 3:1; composants d'interface et graphismes nécessaires à la compréhension au moins 3:1. Références primaires: [WCAG 2.2, critère 1.4.3 Contrast (Minimum)](https://www.w3.org/TR/WCAG22/#contrast-minimum) et [WCAG 2.2, critère 1.4.11 Non-text Contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast). Tout résultat inférieur au seuil applicable est un échec, même si la couleur semble lisible ou si une lueur est présente.
- Appliquer `prefers-reduced-motion`: supprimer déplacements, transitions longues et pulsations non essentielles. Les lueurs doivent rester statiques par défaut; une lueur au hover peut être légère, jamais le seul indicateur de focus ou d'état.
- Utiliser les couleurs et effets D-18: surfaces bleu nuit, accents violet/cyan, bordures peu lumineuses, dégradés localisés et ombres violettes discrètes. Réserver `--shadow-glow-v3` ou les tokens de bouton à un panneau de mise en avant ou à une action prioritaire. Vérifier le contraste après ajout d'une lueur et préserver une surface unie sous le texte.

Les choix d'ordre, densité, valeurs géométriques, seuils exacts et comportement de la navigation mobile sont une baseline réversible à valider pendant la conception des écrans. D-17 approuve le shell commun et D-18 la famille de palette/langage V1; aucune mesure de contraste n'a été effectuée dans ce cadrage. Ces décisions ne valent pas approbation des maquettes, contrastes mesurés ou rendus Dashboard.

## Critères de validation visuelle

1. Préparer une référence V1 et une capture V2 comparables pour la vitrine et Connexion/Inscription; conserver textes, langues, destinations, champs, interactions, validations et états visibles sans différence non approuvée.
2. Couvrir les largeurs et langues du cahier: 320, 390, 768, 1024, 1280, 1440 et 1920 px en FR et EN. Utiliser les mêmes navigateurs, zooms, données et états dans les deux versions; relever les écarts par page.
3. Relire le shell commun, la navigation par rôle et l'adaptation des grilles aux largeurs ciblées. Vérifier les états focus/clavier, contrastes, contrôles de 44 px et `prefers-reduced-motion` dans les sections Viewer et Admin.
4. Confirmer côté serveur les refus d'accès pour les actions Admin; la capture UI n'est pas une preuve d'autorisation.
5. Obtenir la relecture Frontend, QA et Auditeur après les écrans rendus. L'acceptation de D-17 ne valide pas une maquette ou un rendu de Dashboard.

Aucun rendu V2, screenshot, parcours navigateur, calcul de contraste ni image-diff n'est disponible dans ce cadrage. Les critères ci-dessus décrivent les preuves à produire. Les seuls éléments observés sont les sources statiques et tokens V1; les références visuelles n'ont pas été affichées ou comparées dans cette passe.
