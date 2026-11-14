# Suivi GitHub Projects

## Décision et état vérifié

- Choix du propriétaire : GitHub Projects, projet « Skkup V2 ».
- Trello : désactivé.
- État de synchronisation distante : `pending_activation` tant que le projet, ses champs, ses vues et ses éléments n'ont pas été créés puis relus sur GitHub.
- URL et numéro : à renseigner après création vérifiée.

Le dépôt public `Krapaud-Labs/skkup-v2` existe. Le connecteur GitHub présent dans cette session permet les opérations de dépôt, branches, issues et PR; il n'expose pas la gestion GitHub Projects. La CLI GitHub est invalide et la connexion Git du shell échoue sur DNS. La création dans l'interface GitHub reste l'action de reprise nécessaire; aucune synchronisation n'est déclarée réussie.

## Structure visée

Vues proposées : Backlog, En cours, Review et Terminé. Champs à prévoir : Status, Priority, Work item, Owner et Milestone. Les éléments représentent les incréments de conception, d'inventaire de parité V1, d'implémentation par domaine, de validation, puis de livraison. Ne pas créer d'issues tant que le Project ne peut pas les lier et que les critères correspondants ne sont pas prêts.

## Checkpoint local

Le work item local d'initialisation est la source d'avancement actuelle. À l'activation, reporter uniquement les cartes acceptées, relire chaque champ et enregistrer l'identifiant, l'URL et la relecture dans le profil de suivi du dépôt.
