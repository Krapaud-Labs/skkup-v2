# Suivi GitHub Projects

## Décision et état vérifié

- Choix du propriétaire : GitHub Projects, projet « Skkup V2 ».
- Trello : désactivé.
- État distant : projet créé et relu le 2026-11-14; vue configurée, couverture d'issues à compléter après validation de la conception.
- Numéro : 5.
- URL : https://github.com/orgs/Krapaud-Labs/projects/5/views/1
- Visibilité observée : privée (icône de verrouillage). Le dépôt produit est public. La réponse « Public » du cadrage concernait le dépôt, pas une ouverture de visibilité du Project.

Le dépôt public `Krapaud-Labs/skkup-v2` existe. Le Project a été créé via la session GitHub dédiée et relu à l'URL ci-dessus. L'import automatique des issues a été désactivé. Le connecteur API ne propose pas la gestion Projects; l'interface a permis la création.

## Structure visée

La première vue est un Board, et son rendu final vérifié ne montre que les colonnes `Todo`, `In Progress` et `Done`. Les colonnes `Backlog` et `Ready` sont filtrées hors de la vue par défaut; elles ne contiennent aucun élément. Le champ Priority a été ajouté. La vue contient également Title, Assignees, Status, Linked pull requests et Sub-issues progress. Iteration, dates et dépendances restent à configurer si disponibles. Ne pas créer d'issues d'implémentation tant que la readiness de conception est en review.

## Checkpoint local

Le work item local d'initialisation reste la source d'avancement. Après validation de la conception, créer des issues détaillées de couverture MVP/Post-MVP, relire labels, critères, tâches, statuts et liens, puis enregistrer les identifiants et preuves dans le profil de suivi du dépôt.
