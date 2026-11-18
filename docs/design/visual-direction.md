# Direction visuelle et expérience

## Statut

Status: review

## Décisions acceptées

- **Vitrine et Connexion/Inscription :** conserver fidèlement le rendu et les interactions visibles de la V1. Toute différence nécessite une décision propriétaire préalable.
- **Popup de l'extension :** préserver son interface; seules les adaptations d'API sans effet visuel sont prévues.
- **Dashboard :** construire un shell Dashboard commun aux rôles Viewer et Admin, avec une navigation cohérente et des sections/actions affichées selon le rôle. Le backend reste l'autorité des permissions Admin; masquer une action dans l'interface ne remplace pas son contrôle serveur. Décision propriétaire du 2026-11-16, consignée au journal sous D-17.
- **Palette et langage visuel du Dashboard :** réutiliser l'identité V1 bleu nuit, violet et cyan, ses surfaces, dégradés et lumières sélectives. D-18 approuve cette famille visuelle; les détails d'écran et seuils responsive ci-dessous restent une baseline technique réversible.
- **Composition et interactions du Dashboard :** le propriétaire demande une interface professionnelle et agréable dans le thème du site, peu chargée et facile à parcourir, sans défilement global de la page. Toute consultation détaillée et toute édition dans le Dashboard passent par une modale accessible. Les longues listes, tableaux et modales peuvent défiler dans leur propre zone; le document et le shell de page ne défilent pas. Les pages Connexion/Inscription et leur modale d'acceptation du règlement restent régies par la parité V1 du cahier.

## Baseline Dashboard réversible

La référence est `frontend/src/app/design-tokens.css` au commit V1 `Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`. Elle définit le fond `#07132d`, les surfaces `#0d2044` et `#122955`, les accents `#8b3dff` et `#16d9ff`, ainsi que les tokens géométriques/effets `--radius-card: 16px`, `--radius-control: 10px`, `--dashboard-content-gap: 1rem`, `--dashboard-panel-padding: clamp(1rem, 2vw, 1.5rem)` et `--shadow-glow-v3`. D-18 approuve la famille de palette et le langage visuel V1 pour Viewer et Admin; il n'approuve pas ces valeurs geometry/spacing ni leur transposition. Les valeurs V1 citées servent de références candidates; leur adoption dans V2 reste une baseline technique réversible.

### Shell et navigation

- **Desktop, plus de 900 px :** un rail de navigation persistant de 224 à 256 px et une zone de contenu flexible. Le contenu principal ne déborde pas horizontalement; si la liste de destinations dépasse sa hauteur, le rail défile dans sa propre zone. Le titre de page et les actions courantes sont en tête du contenu.
- **900 px et moins :** reprendre le point de bascule V1 où le rail fixe devient une navigation compacte. Sous 600 px, préférer un menu pliable aux rangées défilantes pour respecter l’absence de scroll global; son état ouvert/fermé est annoncé et accessible au clavier. Cette baseline est réversible après prototype.
- Afficher la section courante avec `aria-current="page"`, conserver un ordre de tabulation prévisible, et ramener le focus au bouton déclencheur quand un menu mobile est fermé. La navigation Viewer et Admin partage les mêmes composants et repères; ses liens/actions diffèrent selon le rôle. L'API refuse toute opération Admin non autorisée côté serveur.

### Viewer: ordre des sections de l'accueil

1. **En-tête:** salutation, titre « Tableau de bord » et accès aux actions de compte.
2. **Résumé compact:** solde de points, progression du streak et tickets disponibles, regroupés dans une seule surface cohérente.
3. **À récupérer ou terminer:** une surface prioritaire qui résume les cartes à gratter disponibles et le prochain tirage ouvert; un accès direct ouvre leur détail dans une modale.
4. **Activité et extension:** statut récent regroupé dans une zone synthétique; historique détaillé, état complet d’appairage et progression de session s’ouvrent depuis la navigation et dans leurs modales de consultation.

Navigation Viewer proposée: Vue d'ensemble, Streams, Historique, Récompenses, Tirages, Extension et Compte. Aucun point, ticket ou statut d'appairage ne doit être déduit visuellement s'il n'est pas confirmé par l'API.

### Admin: ordre des sections de l'accueil

1. **En-tête et priorités:** titre, raccourcis de navigation et compteurs agrégés des éléments qui demandent une action.
2. **À traiter:** une file de priorité unique, avec accès aux vues de modération, utilisateurs ou opérations en attente.
3. **Activité récente:** quelques événements d’audit pertinents, avec ouverture du détail dans une modale et lien vers l’historique complet.

Navigation Admin proposée: Vue d'ensemble, Utilisateurs, Modération, Lots, Tirages, Annonces/Contenus, Boutique, Streams/Sponsors et Audit. Les panneaux d'accueil résument et dirigent vers les opérations complètes; ils ne remplacent pas leurs formulaires ou contrôles d'accès.

### Densité, défilement et espacement

- Construire chaque vue Dashboard à l'intérieur de la hauteur disponible du viewport, sans défilement vertical ou horizontal du document. Cette contrainte porte sur la page et le shell, pas sur les contenus longs : leur région dédiée ou leur modale peut défiler indépendamment.
- Garder l'accueil à quelques groupes d'information hiérarchisés et directement actionnables. Les KPI sont synthétiques; les détails ouvrent la section correspondante ou une modale. Ne pas empiler un bloc par indicateur, état ou opération.
- Les consultations détaillées (transactions, récompenses, tirages, objets Admin) et toutes les éditions s'ouvrent en modale sur la route courante. Les modales ont un titre accessible, un focus initial et piégé, Escape/annulation selon le contexte, fermeture explicite, retour du focus au déclencheur et défilement interne si nécessaire. Les créations Admin satisfont également les règles détaillées du cahier §5.9.
- Sur les petites hauteurs et avec le clavier virtuel mobile, la modale reste dans le viewport disponible, son contenu défile à l'intérieur et les actions principales restent accessibles. Les essais de rendu incluent 1440×700 px (fenêtre desktop courte), 390×844 px (mobile standard) et 390×650 px avec clavier virtuel ouvert. À chaque taille, vérifier les états initial, modale longue, erreur de formulaire et liste longue. Ces tailles complètent les largeurs de comparaison du cahier; elles ne changent pas ses critères de parité Auth.

- Utiliser un pas de base de 4 px et les espacements dominants 8, 16, 24 et 32 px. Garder 16 px entre panneaux sur petits écrans et 16 à 20 px sur desktop.
- Garder le padding des panneaux entre 16 et 24 px (`--dashboard-panel-padding`), un inset de contenu de 16 px, un rayon de panneau de 12 px (`--dashboard-radius-panel`) et le rayon de contrôle de 10 px. Le rayon de carte de 16 px s'applique aux grands conteneurs de carte, pas à tous les panneaux.
- Baseline réversible: à partir de 1181 px, conserver une grille Dashboard Viewer à deux zones et des KPIs Admin sur quatre colonnes si leur largeur le permet. De 801 à 1180 px, réduire les KPIs Admin à trois colonnes; à 800 px et moins, à deux, puis une colonne si le contenu est trop étroit. Les tables Admin deviennent des lignes/cartes lisibles; si une table doit défiler horizontalement, le défilement reste limité à son conteneur, jamais au document, sans masquer silencieusement des champs essentiels.

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

La composition peu chargée, l'absence de défilement global et les modales pour consultation détaillée/édition sont des exigences du propriétaire à respecter dans les écrans. Les valeurs géométriques, seuils exacts et comportement de la navigation mobile restent une baseline technique réversible à valider pendant la conception des écrans. D-17 approuve le shell commun et D-18 la famille de palette/langage V1; aucune mesure de contraste n'a été effectuée dans ce cadrage. Ces décisions ne valent pas approbation des maquettes, contrastes mesurés ou rendus Dashboard.

## Critères de validation visuelle

1. Préparer une référence V1 et une capture V2 comparables pour la vitrine et Connexion/Inscription; conserver textes, langues, destinations, champs, interactions, validations et états visibles sans différence non approuvée.
2. Couvrir les largeurs et langues du cahier: 320, 390, 768, 1024, 1280, 1440 et 1920 px en FR et EN. Utiliser les mêmes navigateurs, zooms, données et états dans les deux versions; relever les écarts par page.
3. Relire le shell commun, la navigation par rôle et l'adaptation des grilles aux largeurs ciblées et aux hauteurs courtes. Vérifier l'absence de scroll global, le défilement interne des zones longues, les modales de consultation/édition, les états focus/clavier, contrastes, contrôles de 44 px et `prefers-reduced-motion` dans les sections Viewer et Admin.
4. Confirmer côté serveur les refus d'accès pour les actions Admin; la capture UI n'est pas une preuve d'autorisation.
5. Obtenir la relecture Frontend, QA et Auditeur après les écrans rendus. L'acceptation de D-17 ne valide pas une maquette ou un rendu de Dashboard.

Aucun rendu V2, screenshot, parcours navigateur, calcul de contraste ni image-diff n'est disponible dans ce cadrage. Les critères ci-dessus décrivent les preuves à produire. Les seuls éléments observés sont les sources statiques et tokens V1; les références visuelles n'ont pas été affichées ou comparées dans cette passe.
