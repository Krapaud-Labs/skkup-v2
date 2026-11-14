# Conception de sécurité

Le [modèle de menace](../security/threat-model.md) est la référence pour les actifs, frontières de confiance, scénarios, contrôles et preuves attendues.

## Baseline de cadrage

- Rôles Viewer et Admin vérifiés par l'API pour chaque ressource.
- Sessions, appairage, ledger de points, tirages et opérations Admin conçus contre rejeu et concurrence.
- Secrets injectés à l'exécution; aucun secret ni donnée réelle dans le dépôt ou les exemples.
- Base V2 initialement vide; aucune migration implicite.
- Rétention, suppression/export, récupération, email, origines web et déploiement à spécifier avant les lots concernés.

Ces exigences ne prouvent ni l'audit d'une implémentation ni une conformité juridique.
