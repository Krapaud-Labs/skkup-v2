# Conception de sécurité

Le [modèle de menace](../security/threat-model.md) est la référence pour les actifs, frontières de confiance, scénarios, contrôles et preuves attendues.

## Baseline de cadrage

- Rôles Viewer et Admin vérifiés par l'API pour chaque ressource.
- Sessions, appairage, ledger de points, tirages et opérations Admin conçus contre rejeu et concurrence.
- Secrets injectés à l'exécution; aucun secret ni donnée réelle dans le dépôt ou les exemples.
- Base V2 initialement vide; aucune migration implicite.
- Rétention, suppression/export, récupération, email, origines web et déploiement à spécifier avant les lots concernés.

Ces exigences ne prouvent ni l'audit d'une implémentation ni une conformité juridique.

## État de sécurité Auth/session, lot #5 en cours

Le backend implémente actuellement le hachage des mots de passe par scrypt,
des jetons de session signés HS256 valables 24 heures, une persistance des
sessions en base et les opérations d'inscription, connexion, consultation de
session, déconnexion et changement de mot de passe. Le mot de passe changé
incrémente `session_version` et révoque les sessions web V2 connues. Ces
éléments décrivent le code présent et ne constituent pas encore une validation
indépendante de sécurité ou de parité avec la V1.

Compose exige `AUTH_TOKEN_SECRET` et `COOKIE_SECURE`; le secret doit contenir
au moins 32 octets. `.env.example` fournit une valeur vide à remplacer par un
secret local ignoré par Git, jamais par une clé réelle commise. `AUTH_ALLOWED_ORIGINS`
configure une liste exacte d'origines autorisées et les requêtes d'écriture
d'authentification vérifient `Origin`. Le cookie utilise `HttpOnly`,
`SameSite=Lax`, `Path=/` et `Secure` par défaut; le mode non sécurisé est
réservé au HTTP local. Proxy trust, configuration d'origine de déploiement et
intégration navigateur restent à vérifier.

La limitation d'inscription, de connexion et de changement de mot de passe
est actuellement en mémoire du processus et s'appuie sur l'adresse du client.
Les seuils présents sont 5 inscriptions/heure, 10 tentatives de connexion/minute
et 3 changements de mot de passe/heure.
Elle ne se partage pas entre workers, conteneurs ou redémarrages; un déploiement
multi-worker ou public nécessite un limiteur partagé avant exposition.

La V1 révoque aussi les credentials d'appairage et les sessions de visionnage
lors d'un changement de mot de passe. Ces domaines ne sont pas encore présents
dans le V2 de ce lot. `session_version` est un epoch de révocation prévu pour
les futurs credentials, à inclure et vérifier côté serveur; il ne prouve pas
aujourd'hui la révocation d'extension/watch. Cette parité dépend du lot #7.
La revue du comportement frontend Connexion/Inscription reste en cours.
QA rapporte cinq tests Auth réussis : quatre tests de contrat
ASGI direct avec SQLite en mémoire et un test unitaire du rollover au
changement de jour civil. Ruff sur l'application, les migrations et les tests
passe également. QA a comparé des captures Chromium headless locales V1/V2
desktop, mobile et inscription. Les écarts visuels sont estimés à environ
10–20 px sur mobile et environ 5 px sur la modale selon les vues; aucune mesure
différentielle quantitative n'a été produite et le pixel-perfect n'est pas
revendiqué. Le défilement du CTA de la modale mobile a été vérifié, et vingt
pressions Tab sont restées dans la modale sans soumettre le formulaire. Ces
contrôles ciblés ne constituent pas un audit de sécurité indépendant ni une
intégration PostgreSQL. La migration Compose/PostgreSQL n'a pas été vérifiée
car le socket Docker a refusé l'accès dans l'environnement QA; le lot #5
demeure en cours.
