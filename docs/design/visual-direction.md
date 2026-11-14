# Direction visuelle et expérience

## Statut

Status: review

## Décisions visuelles

- Vitrine et pages Connexion/Inscription : reproduire fidèlement le rendu et les interactions visibles de la V1. Aucun changement esthétique n'est autorisé ici.
- Dashboards Viewer et Admin : nouvelle conception, sans supprimer les capacités ni styles partagés qui altèrent la vitrine.
- Popup de l'extension : interface conservée à l'identique; seules les adaptations d'API sans effet visuel sont permises.
- Palette, typographie, espacement, composants et motion des dashboards : à proposer avant le premier écran. Aucune référence visuelle source n'a été auditée dans cette reprise.

## Principes d'interface

États de chargement, vide, erreur, succès, focus et désactivé explicites; navigation clavier; contraste vérifiable; respect de `prefers-reduced-motion`; responsive à définir après inventaire des vues V1. Préserver textes, destinations et validations des pages conservées.

## Validation visuelle

Captures V1 et matrice des viewports/langues du cahier à établir avant implémentation. La porte finale compare les mêmes navigateurs, zooms, états et données et vise zéro différence non approuvée. Aucun audit visuel n'a été effectué pendant ce cadrage.
