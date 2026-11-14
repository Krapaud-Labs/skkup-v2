# Contrats d'interfaces

## Décisions et limites

API cible REST JSON/OpenAPI avec FastAPI/Pydantic. La compatibilité Socket.IO du client existant est à préserver jusqu'à l'inventaire des contrats et clients publiés. Les domaines ci-dessous sont des frontières de conception, pas des endpoints approuvés.

| Domaine | Consommateur | Responsabilité | Autorisation à spécifier | Preuve avant implémentation |
| --- | --- | --- | --- | --- |
| Authentification/session | site | ouvrir, terminer, consulter une session | compte concerné, anti-abus | contrat V1 et tests négatifs |
| Profil/activité | site | préférences, solde, ledger, streak | propriétaire du compte | règles V1 et invariants |
| Appairage/visionnage | extension | lier appareil, envoyer activité admissible | jeton révocable | routes, payloads, plateformes |
| Récompenses/tirages | site | dépenser, tirer, historiser | rôle Viewer et états métier | transactions et auditabilité |
| Administration | dashboard Admin | gérer utilisateurs et contenus | rôle/ressource côté serveur | matrice d'accès et journal |
| Temps réel | site/extension | notifier changements | handshake, rooms isolées | protocole Socket.IO V1 |

## Conventions à décider au scaffold

Versionnement, erreurs, pagination, idempotence, tailles maximales, délais et retry seront spécifiés en cohérence avec les clients V1. Les réponses n'exposent pas l'existence d'un compte. L'API est la source de vérité des droits, soldes, durées créditées et états de tirage.

## Compatibilité

Ne pas changer les routes ou payloads consommés par l'extension sans versionnement et migration coordonnée. REST permet de récupérer l'état si le temps réel échoue. Les exemples concrets attendent la comparaison au commit V1.
