# Journal qualité

## Règle

Ce journal conserve les anomalies vérifiées, leur impact, leur propriétaire et la preuve de correction. Les limites de cadrage ne sont pas présentées comme défauts applicatifs.

## Registre

Le lot 3 ajoute uniquement le scaffold technique V2; les fonctionnalités Viewer/Admin et les règles métier restent absentes. QA et audit indépendant ont observé puis fait corriger les écarts suivants avant livraison :

| ID | Anomalie observée | Correction et preuve indépendante | Statut |
| --- | --- | --- | --- |
| Q-ISSUE-3-01 | Le downgrade initial supprimait `alembic_version` avant le nettoyage interne d'Alembic, ce qui faisait échouer `alembic downgrade base` avec `UndefinedTable`. | La migration ne supprime plus la table interne. Le smoke QA sur base jetable passe `upgrade head`, `downgrade base`, vérifie zéro ligne et aucune table produit, puis repasse `upgrade head`. | verified |
| Q-ISSUE-3-02 | Le workflow CI manquait concurrence/annulation, déclenchement manuel et garde preflight/sécurité exigés par la politique projet; `commands.test` n'était pas configurée. | Workflow doté de `concurrency`, `workflow_dispatch`, actions épinglées, scripts preflight/sécurité/smoke et commandes de profil vérifiées. QA passe les scripts, la configuration YAML et le smoke isolé. | verified |
| Q-ISSUE-3-03 | Les règles Git ignore ne couvraient pas les environnements locaux, caches Python et sorties Next.js du scaffold. | `.gitignore` étendu; QA vérifie que `.env`/`.env.local`, venv, caches, `node_modules` et `.next` sont ignorés et que `.env.example` reste admissible. | verified |

La CI GitHub distante n'a pas encore été exécutée à ce point de contrôle et reste une porte de livraison avant fusion. Ces contrôles ne constituent pas des tests de fonctionnalités produit. Les autres risques de conception restent dans `docs/project-management/decision-log.md` et `docs/security/threat-model.md`.

## Statuts futurs

`open`, `in-progress`, `fixed`, `verified`, `accepted-risk`, `wont-fix`, `duplicate`, `blocked`. Un élément `fixed` requiert une preuve indépendante pour devenir `verified`.
