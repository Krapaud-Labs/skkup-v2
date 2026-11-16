# Readiness de conception

Status: approved

Portée : cadrage de conception seulement; les préconditions d’implémentation et de release restent définies par lot ci-dessous.

## Portes du cadrage de conception

- [x] Cahier de cadrage accepté; les inconnues localisées restent explicites.
- [x] Vision, stories et parcours rédigés.
- [x] Architecture, données, contrats API et modèle de menace documentés en draft.
- [x] Décisions et roadmap consignées; archive du cahier préservée.
- [x] Inventaire statique de parité V1 relu; les divergences métier de récompenses couvertes sont arbitrées par D-14 à D-16.
- [x] Direction des dashboards et critères visuels de cadrage relus selon D-17 et D-18; les contrôles de rendu restent des préconditions par lot.
- [x] Relecture indépendante du cadrage de conception achevée; Auditeur PASS le 2026-11-16.
- [x] Scan des documents de conception sans marqueur de gabarit restant; PASS le 2026-11-16.

## Portée de l’approbation et préconditions par lot

Cette approbation concerne le **cadrage de conception** : inventaire statique
V1, arbitrages D-14 à D-16, direction de Dashboard D-17/D-18, revue QA et
audit indépendant. Elle autorise la préparation détaillée et la planification
des lots de développement; elle ne certifie ni le rendu ni le comportement
d’une application V2, qui n’est pas encore implémentée.

Conserver les préconditions suivantes dans les lots concernés :

- produire les rendus V2 et vérifier la parité de la vitrine et de
  Connexion/Inscription aux références V1 avant de fermer leurs lots;
- mesurer le responsive et les contrastes sur les écrans V2, et vérifier les
  états clavier/focus avant livraison des interfaces concernées;
- écrire puis exécuter les tests V2 correspondant aux règles et contrats de
  chaque lot;
- avant d’implémenter ou livrer une fonction Admin, prouver les refus d’accès
  côté serveur au moyen de tests négatifs par rôle/action;
- établir la provenance et les droits de chaque média avant toute copie dans
  V2;
- obtenir les décisions requises sur les données de production, la migration,
  l’exploitation et la publication avant toute release ou mise en production.

Les tests V1 cités dans l’inventaire n’ont pas été exécutés. Aucun test V2,
build, comparaison visuelle, mesure responsive/contraste ni contrôle effectif
de permission n’est revendiqué comme exécuté par cette approbation.

## Inventaire de parité V1/V2

Référence examinée par lecture des objets Git, sans checkout, switch, reset ni
modification du checkout V1, qui contient des changements locaux préexistants :
`Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`. Les preuves
ci-dessous signifient que les chemins de code/tests existent dans l’arbre, pas
que leur exécution ou leur comportement déployé a été confirmé. La colonne V2
indique le mapping documentaire et le critère futur, sans prétendre à une
implémentation V2.

#### Comptage reproductible dans l’arbre V1

Lecture statique des objets Git à la SHA ci-dessus: **27 fichiers `page.tsx`**
(routes applicatives), **1 handler `route.ts`** (service d’assets) et **4
layouts**; **19 fichiers controller, 20 classes `@Controller` et 81 routes
HTTP**; **172 fichiers de
tests nommés `.test/.spec` ou `*.e2e-spec` contenant 841 déclarations `it` ou
`test`**; **72 fichiers image** dans `frontend/assets` et `frontend/public`,
dont **44 chemins URL `/assets/` littéraux** dans le code runtime analysé.
S’ajoutent des motifs de chemins scratch générés par code et les icônes
extension copiées au build. Ces nombres comptent les artefacts présents, pas
la couverture utile, le passage des tests, les téléchargements à l’exécution,
ou la publication d’une route/asset.

La commande ci-dessous reproduit le comptage depuis le dépôt V1 voisin,
uniquement par `git ls-tree`/`git show` à la SHA fixée. Elle n’extrait aucun
fichier de travail, ne change pas la branche, et n’exécute aucune suite.

```bash
python3 - <<'PY'
import re, subprocess
repo = '../Skkup'
sha = 'fcc4767f3ece9efc069d1a1c413942067cb89c93'
def paths(root):
    return subprocess.check_output(['git', '-C', repo, 'ls-tree', '-r', '--name-only', sha, '--', root], text=True).splitlines()
def source(path):
    return subprocess.check_output(['git', '-C', repo, 'show', f'{sha}:{path}'], text=True)
app = paths('frontend/src/app')
pages = [p for p in app if p.endswith('/page.tsx') or p == 'frontend/src/app/page.tsx']
handlers = [p for p in app if p.endswith('/route.ts')]
layouts = [p for p in app if p.endswith('/layout.tsx') or p == 'frontend/src/app/layout.tsx']
controllers = [p for p in paths('backend/src') if p.endswith('.controller.ts')]
controller_text = [source(p) for p in controllers]
classes = sum(t.count('@Controller(') for t in controller_text)
endpoints = sum(len(re.findall(r'@(Get|Post|Put|Patch|Delete)\(', t)) for t in controller_text)
roots = ['backend', 'frontend/src', 'frontend/e2e', 'extension/src', 'extension/e2e']
tests = sorted({p for root in roots for p in paths(root) if re.search(r'\.(spec|test)\.(ts|tsx|js|mjs)$', p) or p.endswith('.e2e-spec.ts')})
cases = sum(len(re.findall(r'\b(?:it|test)\s*\(', source(p))) for p in tests)
images = [p for root in ['frontend/assets', 'frontend/public/assets'] for p in paths(root) if re.search(r'\.(png|jpe?g|svg|webp|ico|gif)$', p, re.I)]
runtime_roots = ['frontend/src', 'frontend/public', 'extension/src']
asset_urls = set()
for root in runtime_roots:
    for p in paths(root):
        if not p.endswith(('.tsx', '.ts', '.css', '.scss', '.html', '.json')) or re.search(r'\.(spec|test)\.(ts|tsx|js|mjs)$', p):
            continue
        asset_urls.update(x.split('#')[0].split('?')[0] for x in re.findall(r"[\"'](/assets/[^\"'` )]+)", source(p)))
print(f'pages={len(pages)} route_handlers={len(handlers)} layouts={len(layouts)}')
print(f'controller_files={len(controllers)} controller_classes={classes} http_routes={endpoints}')
print(f'test_files={len(tests)} it_test_declarations={cases}')
print(f'image_files={len(images)} literal_runtime_asset_urls={len(asset_urls)}')
PY
```

| Parcours et actions | Route / source V1 exacte | Code et tests V1 présents | Règle canonique et mapping / critère V2 | Comparaison et état |
| --- | --- | --- | --- | --- |
| Vitrine, navigation, langue, FAQ, règlement, confidentialité, extension publique, streams et tirages publics | `frontend/src/app/{page.tsx,faq/page.tsx,reglement/page.tsx,confidentialite/page.tsx,extension/page.tsx,streams/page.tsx,tirages/page.tsx}`, `frontend/src/app/layout.tsx` | Routes et composants présents; tests frontend à repérer | Cahier §§4, 5.1; `US-01`; `docs/product/user-flows.md`. Critère: mêmes destinations, sections, langue et états aux viewports spécifiés. | Parcours relevé; liens, FR/EN, textes, états et rendu non comparés. Captures/image-diff V2 absents. |
| Inscription, connexion, session, déconnexion, changement de mot de passe et OAuth | `frontend/src/app/{connexion/page.tsx,inscription/page.tsx}`, `backend/src/auth/{auth.controller.ts,auth.service.ts}` | `backend/test/auth-lifecycle.e2e-spec.ts`; specs unitaires `backend/src/auth/*.spec.ts` | Cahier §§4, 5.2; `US-02`; `docs/design/api-contracts.md`. Critère: mêmes champs, validation, erreurs et session; autorisation serveur. | Code/tests présents; aucun test exécuté ni comparaison UI. États et parcours OAuth à comparer. |
| Viewer: résumé, profil, compte et check-in quotidien | `frontend/src/app/dashboard/{page.tsx,compte/page.tsx}`, `backend/src/me/{me.controller.ts,me.service.ts}` | `backend/test/{me-dashboard-viewer.e2e-spec.ts,daily-checkin.e2e-spec.ts}` | Cahier §5.3; `US-03`; D-14. Critère: solde cohérent et check-in idempotent; le ticket classique D-07 au jour 1 satisfait le palier 1 du cahier et remplace les +5 directs, sans gain distinct. | Arbitrage documenté; code/tests V1 présents; aucune exécution ou implémentation V2. |
| Viewer: historique des points et ledger | `frontend/src/app/dashboard/historique/page.tsx`, `backend/src/me/`, `backend/src/watch-sessions/` | Services et contrôleurs présents; `backend/src/me/me.service.spec.ts` | Cahier §5.3; `US-03`; `docs/design/data-model.md`. Critère: chaque mouvement daté, catégorisé et réconciliable au solde. | Historique identifié; colonnes, pagination, états et invariants à comparer. |
| Viewer: récompenses, inventaire et cartes à gratter | `frontend/src/app/dashboard/recompenses/page.tsx`, `backend/src/scratch-cards/{scratch-cards.controller.ts,scratch-cards.service.ts}` | `backend/test/scratch-card-no-win.e2e-spec.ts`; `backend/src/scratch-cards/scratch-cards.service.spec.ts` | Cahier §5.6; `US-05`; D-08/D-16. Critère: résultat V1 conservé selon D-08; ticket de grattage catégorisé classique. | Décision inscrite; tests V1 présents mais non lancés; équivalence V2 et cas ticket à tester. |
| Viewer: tirages, inscription, tickets et résultats | `frontend/src/app/dashboard/tirages/page.tsx`, `backend/src/raffles/{raffles.controller.ts,raffles.service.ts}`, `backend/src/me/` | `backend/test/raffle-admin-draw.e2e-spec.ts`; specs `backend/src/raffles/*.spec.ts` | Cahier §§5.6-5.7; `US-05`; `docs/design/api-contracts.md`. Critère: états ouverts/passés, inscription autorisée, historique et résultat consultable. | Sources relevées; états/règles et auditabilité V2 non vérifiés. |
| Viewer: boutique et achats | `frontend/src/app/dashboard/boutique/page.tsx`, `backend/src/shop/{shop.controller.ts,me-shop.controller.ts,shop.service.ts}` | `backend/src/shop/shop.service.spec.ts` | Cahier §5.8; `US-05`; D-10. Critère: disponibilité, prix/stock, achat concurrent et achat consultable respectent statuts. | Boutique maintenue en développement; parcours/actions et tests non comparés. |
| Viewer: streams et récompenses associées | `frontend/src/app/dashboard/streams/page.tsx`, `frontend/src/app/streams/page.tsx`, `backend/src/streams/` | Specs `backend/src/streams/streams.{controller,service}.spec.ts` | Cahier §5.4; `US-04`; D-09. Critère: seules plateformes retenues déclenchent un crédit admissible. | Code présent; plateformes prises en charge et détails de parité à vérifier. |
| Appairage/révocation, ouverture, heartbeat et clôture des sessions | `frontend/src/app/dashboard/extension/page.tsx`, `backend/src/extension/extension.controller.ts`, `backend/src/watch-sessions/watch-sessions.controller.ts`, `extension/src/commun/endpoints.ts` | `backend/test/{extension-pairing.e2e-spec.ts,watch-session-heartbeat.e2e-spec.ts}` | Cahier §§5.4-5.5; `US-04`; décisions D-03/D-04. Critère: contrats consommés compatibles, révocation effective et session éligible idempotente. | Tests présents; non exécutés; payloads, cas limites et clients publiés non comparés. |
| Popup: appairage, état de connexion, compte et progression | `extension/src/popup/{popup.html,popup.ts,popup.css,code-appariement.ts,progression.ts}` | `extension/src/popup/{code-appariement.test.ts,progression.test.ts}` | Cahier §4.2; `US-04`. Critère: mêmes écrans, textes, états, saisie code et progression. | Interface à conserver; tests non exécutés et fidélité visuelle non inspectée. |
| Worker, scripts de contenu, détection vidéo, cadence et plateformes | `extension/src/{arriere-plan/,contenu/,commun/,manifeste.ts}`; motifs `twitch.tv`, `youtube.com`, `kick.com`, `www.kick.com` | Tests `orchestrateur.test.ts`, `detecteur-lecture.test.ts`, `selection-video.test.ts`, `cadence.test.ts`, `plateformes.test.ts`; `extension/README.md` déclare Chrome uniquement en V1.0, Firefox/Opera comme intention V1.1 | Cahier §§4, 5.4-5.5; `US-04`; D-09. Critère: comportement de mesure et éligibilité équivalents pour plateformes autorisées. | Code décrit Twitch/YouTube/Kick et Chrome V1; README/test local Chromium ne prouvent ni publication Store ni parc client réel. Firefox/Opera non confirmés; OS réellement publiés inconnu. |
| Calcul des points de visionnage, plafond et idempotence | `backend/src/watch-sessions/watch-sessions.service.ts`, `backend/src/streams/` | `backend/test/watch-session-heartbeat.e2e-spec.ts`, `backend/src/watch-sessions/watch-sessions.service.spec.ts` | Cahier §§5.3-5.4; `US-03/04`; D-07/D-08. Critère: barème horaire et plafond visionnage respectés sans doubles crédits. | Barème V1 confronté au visuel; aucun test exécuté; plafond global multi-sources inconnu. |
| Streak et récompenses des paliers 3/7/14/30 | `backend/src/me/me.service.ts`, `backend/test/daily-checkin.e2e-spec.ts` | Code et test e2e présents | Cahier §5.3; `US-03/05`; D-14/D-15. Critère: tickets D-07 ajoutés aux cartes V1 préservées conformément à D-08. | Arbitrages consignés; composition conjointe attend tests V2, non exécutés. |
| Admin: cockpit, utilisateurs, rôles, statuts, modération et audit | `frontend/src/app/admin/{page.tsx,users/page.tsx,moderation/page.tsx,audit/page.tsx}`, `backend/src/{admin-dashboard/,admin-users/,fraud-flags/}` | Specs services correspondants; tests des guards dans `backend/src/auth/guards/` | Cahier §5.9; `US-06`; `docs/security/threat-model.md`. Critère: actions par rôle, refus serveur, validations et journal d’audit conformes. | Capacités recensées; matrice action-permission et écrans détaillés à comparer. |
| Admin: lots, tirages, annonces et contenus | `frontend/src/app/admin/{lots/page.tsx,raffles/page.tsx,announcements/page.tsx}`, `backend/src/{admin-lots/,raffles/admin-raffles.controller.ts,announcements/,content/}` | Specs contrôleur/services dans les domaines; `backend/test/{raffle-admin-draw.e2e-spec.ts,announcements-lifecycle.e2e-spec.ts}` | Cahier §§5.1, 5.7, 5.9; `US-06`. Critère: formulaires, statuts, validations et historique correspondants, opérations Admin autorisées uniquement. | Sources/tests existants; aucun lancement, comparaison de formulaire ou matrice exhaustive effectué. |
| Admin: boutique, sponsors et lots associés | `frontend/src/app/admin/shop/page.tsx`, `backend/src/{shop/admin-shop.controller.ts,sponsors/}` | `backend/src/shop/shop.service.spec.ts`; specs de sponsors présentes | Cahier §§5.8-5.9; `US-06`; D-10. Critère: gestion autorisée des articles, stock, codes et liens vers tirages/lots. | Existence confirmée; transitions, actions et permissions restent à rapprocher. |
| Temps réel: handshake, rooms, événements, redis adapter | `backend/src/realtime/{realtime.gateway.ts,realtime.constants.ts,realtime.service.ts,redis-socket.adapter.ts}` | `backend/test/realtime-redis-adapter.e2e-spec.ts`; specs `backend/src/realtime/*.spec.ts` | Cahier §5.10; `US-03` à `US-06`; D-04; `docs/design/api-contracts.md`. Critère: événements/payloads isolés par room, reconnexion et récupération REST. | Preuves présentes; aucun test exécuté; charges utiles par client et compatibilité publiées non auditées. |
| Contrats REST entre backend et extension | `backend/src/{extension/,watch-sessions/}`, `extension/src/commun/{api.ts,endpoints.ts}` | Tests d’appairage et heartbeat précités | Cahier §§4, 5.4-5.5; `US-04`; D-03. Critère: routes et payloads consommés préservés ou versionnés. | Routes trouvées; inventaire exhaustif endpoints/payloads et compatibilité restent ouverts. |
| Données, contraintes, migrations et historique | `backend/prisma/schema.prisma`, `backend/prisma/migrations/`, services métier cités | Schéma/migrations présents; tests de domaines ci-dessus | Cahier §§4, 5, 8; `docs/design/data-model.md`; `US-03/05/06`. Critère: traduire contraintes, unicités, transactions, historiques sans migration implicite des données prod. | Présence V1 confirmée; correspondance V2 et inventaire de prod non établis. |
| Suites de tests existantes (couverture transversale) | `backend/test/`, specs `backend/src/`, tests `extension/src/`, `frontend/e2e/` | Fichiers listés par parcours; `frontend/e2e/dashboard-account-functional.spec.ts` | Cahier §3; `US-01` à `US-07`. Critère: tests V2 couvrant critères métier, permissions, négatifs et parcours UI. | Présence seulement; aucun test ni build lancé, aucun résultat revendiqué. Couverture frontend exacte à compléter. |
| Environnement isolé, Docker, migrations, healthchecks et CI | `docker-compose*.yml`, `backend/Dockerfile*`, `frontend/Dockerfile`, workflows CI et scripts de déploiement V1 | Fichiers d’exploitation présents dans le commit; aucune exécution | Cahier §8; `US-07`; roadmap phase environnement. Critère: V2 isolée, base vide, migrations reproductibles, healthchecks et CI verte. | Pas une route applicative; équivalence d’exploitation V1/V2 non auditée et contrôles non lancés. |
| Images, icônes, médias, styles et actifs utilisés par le rendu | `frontend/src/components/navigation/{EnteteVitrine.tsx,NavigationGlobale.tsx}`; `components/i18n/{LocalizedHomeHero.tsx,LocalizedHomeSteps.tsx,LocalizedDashboardExtensionPage.tsx}`; `components/dashboard/TableauDeBord.tsx`; `components/ui/SkkupIcon.tsx`; `lib/scratch-card-reward.ts`; popup manifeste/HTML | Chemins référencés par le code; assertions de chemins/hash présents notamment dans `SkkupIcon.test.tsx`, `TableauDeBord.test.tsx`, tests i18n et `scratch-card-mask.test.ts` | Cahier §§4.1-4.2; `docs/design/media-inventory.md`; `US-01`. Critère: inventaire par actif avec source, usage réel, SHA-256, dimensions et provenance avant copie. | Les chemins runtime littéraux, chemins générés et copies package repérés sont consolidés dans l’inventaire média. La provenance/licence individuelle et les droits restent inconnus; aucun actif V1 ne peut être copié avant leur preuve. |

### Index de chaque route frontend

Les 27 routes fichier ci-dessous sont celles `page.tsx` de l’arbre V1. Le
handler dynamique `frontend/src/app/assets/[...path]/route.ts` est listé en
note après la table. Les pages délèguent souvent à des composants; les noms
indiqués sont les imports principaux vérifiés dans leur source. Quand une page
ne possède pas de test de route propre, les preuves sont les tests du
composant/client cité, s’ils existent; aucune couverture n’est supposée.

| URL | Page et appelant principal | Story / règle V2 | Preuve de test source et statut |
| --- | --- | --- | --- |
| `/` | `app/page.tsx`; `EnteteVitrine`, contrôleurs de scroll, hero localisé | `US-01`; cahier §§4, 5.1; D-02 | `app/page.test.tsx` présent; pas de comparaison V1/V2 exécutée. |
| `/faq` | `app/faq/page.tsx`; `FaqContent`, `lib/api` | `US-01`; cahier §5.1 | Tests `FaqContent` présents; contenu/rendu non comparés. |
| `/reglement` | `app/reglement/page.tsx`; `ReglementPublicContent` | `US-01`; cahier §5.1 | Tests de contenu/règles présents; comparaison complète non faite. |
| `/confidentialite` | `app/confidentialite/page.tsx`; `ConfidentialiteContent` | `US-01`; cahier §5.1 | `ConfidentialiteContent.test.tsx` présent; non exécuté. |
| `/extension` | `app/extension/page.tsx`; `CodeAppariement`, `LocalizedExtensionIntro` | `US-01/04`; cahier §§4.2, 5.4-5.5 | Tests d’appairage frontend/backend présents; pas lancés. |
| `/streams` | `app/streams/page.tsx`; `ListeStreams`, badges et page intro localisée | `US-01/04`; cahier §§5.1, 5.4 | `ListeStreams.test.tsx`, `PlateformeBadge.test.tsx` présents; non exécutés. |
| `/tirages` | `app/tirages/page.tsx`; `ListeTirages` | `US-01/05`; cahier §§5.1, 5.7 | `ListeTirages.test.tsx` présent; non exécuté. |
| `/connexion` | `app/connexion/page.tsx`; `FormulaireAuth` | `US-02`; cahier §5.2; D-02 | Tests FormulaireAuth/auth présents; viewport, textes et erreurs non comparés. |
| `/inscription` | `app/inscription/page.tsx`; `FormulaireAuth` | `US-02`; cahier §5.2; D-02 | Tests FormulaireAuth/auth présents; viewport, textes et erreurs non comparés. |
| `/dashboard` | `app/dashboard/page.tsx`; `TableauDeBord`, `lib/dashboard` | `US-03/04`; cahier §5.3 | `TableauDeBord.test.tsx`, tests dashboard présents; non exécutés. |
| `/dashboard/admin` | `app/dashboard/admin/page.tsx`; garde/navigation serveur vers Admin | `US-06`; cahier §5.9; D-11 | Guards Admin tests présents; chemin/redirect V1 non comparé. |
| `/dashboard/boutique` | page; `BoutiqueViewer`, `lib/shop` | `US-05`; cahier §5.8; D-10 | Tests `shop.service.spec.ts`, tests ShopAdmin; Viewer UI case mapping à confirmer. |
| `/dashboard/compte` | page; `CompteViewer`, `lib/auth`/profile | `US-02/03`; cahier §5.2-5.3 | Tests auth/profile présents; erreurs et états compte non comparés. |
| `/dashboard/extension` | page; `LocalizedDashboardExtensionPage`, client extension | `US-04`; cahier §§5.4-5.5; D-03 | Tests appairage et composant i18n présents; non exécutés. |
| `/dashboard/historique` | `app/dashboard/historique/page.tsx`; redirige vers `/dashboard#history` | `US-03`; cahier §5.3 | `HistoriquePointsViewer.test.tsx` présent pour le composant cible; route redirect non comparée. |
| `/dashboard/recompenses` | page; `CentreRecompenses`, scratch-card client | `US-05`; cahier §5.6; D-08/D-16 | tests scratch card/service présents; non exécutés. |
| `/dashboard/reglement` | page; composants intro/règles localisés | `US-03`; cahier §5.3 | tests composants de règles présents; page non comparée. |
| `/dashboard/streams` | `app/dashboard/streams/page.tsx`; redirige vers `/dashboard` | `US-04`; cahier §5.4; D-09 | `TableauDeBord.test.tsx`/tests streams présents pour surfaces cibles; route redirect non comparée. |
| `/dashboard/tirages` | page; `ListeTirages`, tirages Viewer | `US-05`; cahier §§5.6-5.7 | `ListeTirages.test.tsx`, raffle backend tests présents; non exécutés. |
| `/admin` | page cockpit; API Admin dashboard et navigation | `US-06`; cahier §5.9; D-11 | `app/admin/page.test.tsx`, `AdminSas` tests présents; permissions/pages UI à comparer. |
| `/admin/announcements` | page; `AnnouncementsAdminV3` | `US-06`; cahier §§5.1, 5.9 | `AnnouncementsAdminV3.test.tsx`, lifecycle e2e présent; non exécutés. |
| `/admin/audit` | page; `AdminSectionPage`/`AuditAdminV3` | `US-06`; cahier §5.9 | `AuditAdminV3.test.tsx` présent; non exécuté. |
| `/admin/lots` | `app/admin/lots/page.tsx`; redirige vers `/admin/shop` | `US-06`; cahier §5.9 | Tests ShopAdmin présents pour destination; redirect de compatibilité non comparée. |
| `/admin/moderation` | page; `ModerationAdminV3` | `US-06`; cahier §5.9 | `ModerationAdminV3.test.tsx` présent; non exécuté. |
| `/admin/raffles` | page; `AdminSectionPage`/`RafflesAdminV3` | `US-05/06`; cahier §§5.7, 5.9 | `RafflesAdminV3.test.tsx`, `raffle-admin-draw.e2e-spec.ts` présents; non exécutés. |
| `/admin/shop` | page; `ShopAdminV3` | `US-05/06`; cahier §5.8; D-10 | `ShopAdminV3.test.tsx`, `shop.service.spec.ts` présents; non exécutés. |
| `/admin/users` | page; `UsersAdminV3` | `US-06`; cahier §5.9 | `UsersAdminV3.test.tsx` présent; non exécuté. |

`/assets/[...path]` est le handler `route.ts`, pas une page produit; il sert
les fichiers référencés et vérifie les chemins. Les pages sont toutes
inventoriées, mais appel API détaillé, réponse réelle, erreurs de chaque champ
et traduction FR/EN ne sont pas couverts exhaustivement ligne par ligne.

### Routes API et actions Admin relevées statiquement

Les chemins ci-dessous sont relatifs aux décorateurs NestJS du commit cité;
`backend/src/main.ts` n’ajoute pas de préfixe global. Les DTO cités identifient
le payload source sans transcrire ici tous leurs champs. La présence d’une
route ne prouve ni sa consommation par une version publiée ni sa parité V2.

| Surface / action | Méthodes et routes | Payload ou résultat observé | Preuve / limites |
| --- | --- | --- | --- |
| Auth/session | `GET /auth/session`; `POST /auth/register`; `POST /auth/login`; `PATCH /auth/password`; `POST /auth/logout` | `RegisterDto`, `LoginDto`, `ChangePasswordDto`; register/login posent cookie httpOnly et renvoient le pseudo; logout efface même une session non valide. Services OAuth Google/Facebook/Twitch séparés. | `backend/test/auth-lifecycle.e2e-spec.ts`, DTO/auth et specs OAuth présents. États de formulaires, erreurs/champs et rendu exacts à confronter; aucun test exécuté. |
| Viewer | `GET /me`; `GET /me/dashboard/summary`; `GET /me/points/history`; `GET /me/rewards-summary`; `GET /me/raffle-tickets`; `POST /me/raffles/:raffleId/register`; `POST /me/daily-checkin` | Pagination history/tickets via `page` et `limit`; rewards via `limit`; check-in sans body; services renvoient profil, agrégat, ledger, récompenses, tickets et statut. | `me-dashboard-viewer.e2e-spec.ts`, `daily-checkin.e2e-spec.ts`, service specs présents. Scénarios répétition, gap/streak et paliers définis dans les tests, non lancés. |
| Extension: association | `POST /extension/pairing-token`; `POST /extension/pair`; `GET /extension/pairings`; `DELETE /extension/pairings/:id` | Session web pour générer; `PairDto` pour échange; lister et révoquer les appareils. | `extension-pairing.e2e-spec.ts` et guard/service specs. Identifiants/payloads et réponses d’erreur doivent être confrontés au code client publié. |
| Extension: temps visionné | `POST /watch-sessions`; `POST /watch-sessions/:id/heartbeat`; `POST /watch-sessions/:id/close` | `OuvrirSessionDto`, `HeartbeatDto`; bearer credential côté extension; ouvre, crédite et ferme une session. | `watch-session-heartbeat.e2e-spec.ts` et tests service/guard présents. Duplication, ordre et refus credential ont des scénarios; aucun test exécuté ni payload comparé ligne à ligne. |
| Admin: cockpit et comptes | `GET /admin/dashboard/summary`; `GET /admin/users`; `GET /admin/users/:id`; `GET /admin/users/:id/audit`; `PATCH /admin/users/:id/status` (`UpdateUserStatusDto`) | Liste utilisateurs accepte query `search`; KPIs, détail, audit et mutation de statut. | Sources `admin-dashboard/`, `admin-users/`; tests `UsersAdminV3`, `AuditAdminV3`, `AdminSas`. État chargement, refus 403, filtre/détail établis par assertions statiques; actions UI à rapprocher. |
| Admin: signalements / modération | `GET /admin/fraud/flags`; `GET /admin/fraud/flags/:id`; `PATCH /admin/fraud/flags/:id` (`UpdateFraudFlagDto`) | File, détail, qualification d’un signalement. | `ModerationAdminV3` tests couvrent détail, 403, filtres, pagination et contrôles accessibles; exécution non faite. |
| Admin: lots | `GET /admin/lots`; `GET /admin/lots/:id`; `POST /admin/lots` (`CreateAdminLotDto`); `PATCH /admin/lots/:id` (`UpdateAdminLotDto`); `DELETE /admin/lots/:id` | Liste accepte query `search`; détail et CRUD lots, avec données liées aux formulaires. | `LotsAdminV3` et `AdminSectionPage` tests couvrent création/modification, filtre, chargement, image vide/cassée/fallback, valeur/fournisseur et 403. Tous champs/validations restent à mapper DTO par DTO. |
| Admin: annonces | `POST /admin/announcements` (`CreateAnnouncementDto`); `GET /admin/announcements`; `PATCH /admin/announcements/:id` (`UpdateAnnouncementDto`); `POST /admin/announcements/:id/publish`; `GET /admin/announcements/:id/history`; `POST /admin/announcements/:id/restore/:eventId`; `DELETE /admin/announcements/:id` | Brouillon, édition, publication explicite, historique, restauration et archivage. | `AnnouncementsAdminV3` tests couvrent transitions, expirées, erreur chargement, 403; `announcements-lifecycle.e2e-spec.ts` présent. L’exécution est absente. |
| Admin: contenus | `GET /admin/content`; `GET /admin/content/audit`; `POST /admin/content` (`ContentDto`); `PATCH /admin/content/:id`; `POST /admin/content/:id/publish`; `POST /admin/content/:id/unpublish`; `GET /admin/content/:id/versions`; `POST /admin/content/:id/restore/:versionId` | CRUD, journal, publication/dépublication et restauration versionnée. | `content.controller.ts`, service/controller specs présents. Énumération des champs/validations et couverture UI par action à compléter. |
| Admin: tirages | `GET /admin/raffles`; `GET /admin/raffles/:id/history`; `POST /admin/raffles` (`CreateRaffleDto`); `PATCH /admin/raffles/:id`; `POST /admin/raffles/:id/draw` | Gestion, historique et exécution d’un tirage. | `RafflesAdminV3`/`AdminSectionPage` assertions sur prérequis, état vide, chargement, tirage ouvert et 403; `raffle-admin-draw.e2e-spec.ts` présent, non exécuté. |
| Admin / Viewer: boutique et codes | Admin: `GET /admin/shop/items`; `POST /admin/shop/items` (`CreateShopItemDto`); `PATCH /admin/shop/items/:id` (`UpdateShopItemDto`); `DELETE /admin/shop/items/:id`; `POST /admin/shop/items/:id/codes` (`ImportShopCodesDto`); `GET /admin/shop/purchases`. Viewer: `GET /shop/items`; `POST /shop/purchase` (`PurchaseShopItemDto`); `GET /me/shop/purchases`; `GET /me/shop/purchases/:id/code` | CRUD article, import codes, achat, liste achats et restitution au propriétaire. | `ShopAdminV3`, `shop.service.spec.ts`; test protège l’affichage/stockage du code secret. États prix/stock/concurrence et D-10 restent à valider. |
| Admin: sponsors et récompenses de streams | `GET /admin/sponsors`; `POST /admin/sponsors` (`CreateSponsorDto`); `PATCH /admin/sponsors/:id` (`UpdateSponsorDto`); `GET /streams`; `PATCH /streams/admin/:id/reward` (`UpdateStreamRewardDto`) | CRUD sponsors, liste streams, réglage récompense. | Sources et tests de domaine présents; correspondance exhaustive des formulaires/erreurs UI et historique reste à faire. |
| Public: contenus, annonces, tirages, streams | `GET /content/:type/:slug`; `GET /announcements/active`; `GET /viewer/announcements`; `POST /viewer/announcements/unread-count`; `GET /raffles`; `GET /raffles/:id`; `GET /raffles/:id/result`; `GET /raffles/:id/participants`; `GET /streams` | Lecture contenus, annonces, résultats/participants et liste streams. | Controller/services et tests de domaine présents. Pagination, états vides, champs réellement publics et données dynamiques restent à rapprocher des vues. |
| État service et compteurs publics | `GET /`; `GET /health`; `GET /public/stats` dans `backend/src/app.controller.ts` | Racine/health/statistiques publiques; la source indique objets de retour à relier aux consommateurs et à l’usage opérationnel. | `app.controller.spec.ts`, `app.e2e-spec.ts` présents; caller exact de health et stats à confirmer. `US-01/07`; aucun test lancé. |
| Cartes à gratter Viewer | `GET /me/scratch-cards`; `POST /me/scratch-cards/:id/prepare`; `POST /me/scratch-cards/:id/scratch` dans `backend/src/scratch-cards/scratch-cards.controller.ts` | Liste cartes, préparation et validation du grattage pour carte disponible. | `scratch-card-no-win.e2e-spec.ts`, service specs; `CentreRecompenses`, `ScratchCardModal`. `US-05`, D-08/D-16; scénarios non exécutés. |

#### Appelants des endpoints par contrôleur

Les chemins de tous les **81 endpoints** sont listés ci-dessus par domaine,
les routes de santé/statistiques et scratch cards étant les deux dernières lignes.
Ce répertoire joint les groupes de routes à leurs consommateurs statiques
connus. Un mapping d’appelant signifie présence d’un chemin/client dans les
objets source; il ne démontre pas que l’appel a été observé en production.

| Contrôleur et toutes ses routes | Appelant UI / client V1 repéré | Story / règle / critère V2 |
| --- | --- | --- |
| `admin-dashboard`: `GET /admin/dashboard/summary` | Cockpit `/admin`, `frontend/src/lib/admin.ts` | `US-06`; KPIs Admin selon §5.9, rôle validé serveur. |
| `admin-lots`: list/detail/create/patch/delete sous `/admin/lots` | `LotsAdminV3`, `AdminSectionPage`, `lib/admin.ts` | `US-06`; mêmes actions, validations et historique utiles (§5.9). |
| `admin-users`: list/detail/audit/status sous `/admin/users` | `UsersAdminV3`, `AuditAdminV3`, `lib/admin.ts` | `US-06`; recherche, détail, statut, accès/refus serveur (§5.9). |
| `announcements`: public/Viewer `GET /announcements/active`, `GET /viewer/announcements`, `POST /viewer/announcements/unread-count`; Admin CRUD/publish/history/restore/archive sous `/admin/announcements` | `FaqContent`/centre notifications; `AnnouncementsAdminV3`; `lib/api.ts`, `lib/admin.ts`, announcement client | `US-01/03/06`; contenu publié visible; compteur/états et cycle de vie (§5.1/5.9). |
| `app`: `GET /`, `GET /health`, `GET /public/stats` | Layout/site pour stats publiques; infrastructure/supervision pour health; caller individuel à confirmer | `US-01` pour stats publiques, `US-07` pour health. Contrat retour et consommateur exact incomplets. |
| `auth`: session/register/login/password/logout sous `/auth` | `FormulaireAuth`, `ChangerMotDePasse`, `frontend/src/lib/auth.ts` | `US-02`; préserver session, champs, validation et erreurs visibles (§5.2). |
| `content`: public `GET /content/:type/:slug`; Admin list/audit/create/patch/publish/unpublish/versions/restore sous `/admin/content` | pages publiques `faq`, règlement/confidentialité; contenu Admin via `lib/admin.ts`/`AdminSectionPage` (caller exact par action à confirmer) | `US-01/06`; préserver contenu public/versioning et mutations Admin (§5.1/5.9). |
| `extension`: pairing-token/pair/pairings/revoke sous `/extension` | `CodeAppariement`, page `/extension`, page dashboard extension, `frontend/src/lib/extension.ts`, `extension/src/commun/endpoints.ts` | `US-04`; D-03; mêmes chemins/payloads consommés (§5.4-5.5). |
| `fraud-flags`: list/detail/patch sous `/admin/fraud/flags` | `ModerationAdminV3`, `lib/admin.ts` | `US-06`; file, qualification, permissions et audit (§5.9). |
| `me`: profil/dashboard/history/rewards/tickets/register/check-in sous `/me` | `TableauDeBord`, `HistoriquePointsViewer`, `CentreRecompenses`, client `frontend/src/lib/dashboard.ts` | `US-03/05`; D-14..D-16; solde/ledger/streak et critères §5.3/5.6. |
| `raffles/admin`: CRUD/history/draw sous `/admin/raffles` | `RafflesAdminV3`, `AdminSectionPage`, `lib/raffles.ts`/`lib/admin.ts` | `US-05/06`; tirage contrôlé, prérequis, audit (§5.7/5.9). |
| `raffles/public`: list/detail/result/participants sous `/raffles` | `ListeTirages` sur `/tirages` et `/dashboard/tirages`, client `frontend/src/lib/raffles.ts` | `US-01/05`; données publiques, inscriptions et résultats (§5.1/5.7). |
| `scratch-cards`: `GET /me/scratch-cards`, `POST /me/scratch-cards/:id/prepare`, `POST /me/scratch-cards/:id/scratch` | `CentreRecompenses`, `ScratchCardModal`, client rewards | `US-05`; D-08/D-16; états et résultat scratch de §5.6. |
| `shop/admin`: list/create/update/delete/import codes/purchases sous `/admin/shop` | `ShopAdminV3`, `frontend/src/lib/shop.ts` | `US-05/06`; champs/stock/codes et restrictions (§5.8). |
| `shop/me`: achats et code sous `/me/shop/purchases` | `BoutiqueViewer`, menu compte, `lib/shop.ts` | `US-05`; accès aux codes par le propriétaire, D-12 (§5.8). |
| `shop/public`: list/purchase sous `/shop` | `BoutiqueViewer`, `lib/shop.ts` | `US-05`; prix, stock, achat atomique, D-10 (§5.8). |
| `sponsors`: list/create/update sous `/admin/sponsors` | Admin lots/tirages; caller concret par écran à confirmer | `US-06`; sponsor et association de lots (§5.9). |
| `streams`: list et update reward sous `/streams` | `ListeStreams`, dashboard Viewer; client `frontend/src/lib/streams.ts` | `US-01/04/06`; plateformes et récompense admissibles, D-09 (§5.4). |
| `watch-sessions`: create/heartbeat/close sous `/watch-sessions` | `frontend/src/lib/watch-sessions.ts`, worker `extension/src/arriere-plan/`, client `extension/src/commun/api.ts` | `US-04`; D-03/D-04; contrat client, points et eligibility (§5.4). |

Le compte automatique des décorateurs retrouve 81 routes réparties sur les
19 fichiers et 20 classes controller, y compris le root, le healthcheck, les statistiques publiques
et les trois actions scratch. Les consommateurs du endpoint racine et du
healthcheck ne sont pas complètement identifiés dans l’arbre applicatif.

#### Index route par route: 81 actions HTTP

Les requêtes/guards ci-dessous proviennent des signatures et décorateurs des
20 blocs `@Controller`. Les champs DTO indiqués sont des noms et types source;
ils n’incluent pas toute la sémantique des validateurs. Le guard affiché est
explicite au niveau classe/méthode; `aucun explicite; inconnu` ne prouve pas
qu’une action est anonyme en environnement réel. Les retours sont les types
client V1 lorsqu’identifiés; le backend déclare rarement un DTO de réponse.
Un générique TypeScript n’est donc pas une preuve du JSON servi, et les formes
non réconciliées restent unknown. Chaque ligne cite les sources de tests
présentes, sans affirmer leur exécution ni leur couverture exhaustive.

| Route | Handler V1 | Caller UI/client V1 | Requête et champs DTO | Guard/HTTP | Réponse typée ou unknown | Tests source et critère V2 / limite |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /` | `backend/src/app.controller.ts#getHello` | caller unknown (no direct UI caller found) | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | string | app.controller.spec.ts; app.e2e-spec.ts; US-01/07; §§5.1, 8; root/operations behavior. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/announcements` | `backend/src/announcements/announcements.controller.ts#listerAdmin` | AnnouncementsAdminV3; lib/admin.ts | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/announcements` | `backend/src/announcements/announcements.controller.ts#creer` | AnnouncementsAdminV3; lib/admin.ts | Body dto: CreateAnnouncementDto [titre:string, texte:string, debutAt:string, finAt:string] | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `DELETE /admin/announcements/:id` | `backend/src/announcements/announcements.controller.ts#supprimer` | AnnouncementsAdminV3; lib/admin.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/announcements/:id` | `backend/src/announcements/announcements.controller.ts#modifier` | AnnouncementsAdminV3; lib/admin.ts | Param id: string; Body dto: UpdateAnnouncementDto [titre:string, texte:string, actif:boolean, debutAt:string, finAt:string] | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/announcements/:id/history` | `backend/src/announcements/announcements.controller.ts#historique` | AnnouncementsAdminV3; lib/admin.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/announcements/:id/publish` | `backend/src/announcements/announcements.controller.ts#publier` | AnnouncementsAdminV3; lib/admin.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/announcements/:id/restore/:eventId` | `backend/src/announcements/announcements.controller.ts#restaurer` | AnnouncementsAdminV3; lib/admin.ts | Param id: string; Param eventId: string | `AdminGuard, PostAuthThrottlerGuard` | AnnonceAdmin/AnnonceAdmin[]/EvenementAnnonceAdmin[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/content` | `backend/src/content/content.controller.ts#lister` | CRUD caller unknown; lib/admin.ts audit helper only | Query query: ContentQueryDto [type:ManagedContentType, locale:string] | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/content` | `backend/src/content/content.controller.ts#creer` | CRUD caller unknown; lib/admin.ts audit helper only | Body dto: CreateContentDto [slug:string, type:ManagedContentType, locale:string, data:Record<string, unknown>] | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/content/:id` | `backend/src/content/content.controller.ts#modifier` | CRUD caller unknown; lib/admin.ts audit helper only | Param id: string; Body dto: UpdateContentDto [data:Record<string, unknown>] | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/content/:id/publish` | `backend/src/content/content.controller.ts#publier` | CRUD caller unknown; lib/admin.ts audit helper only | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/content/:id/restore/:versionId` | `backend/src/content/content.controller.ts#restaurer` | CRUD caller unknown; lib/admin.ts audit helper only | Param id: string; Param versionId: string | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/content/:id/unpublish` | `backend/src/content/content.controller.ts#depublier` | CRUD caller unknown; lib/admin.ts audit helper only | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/content/:id/versions` | `backend/src/content/content.controller.ts#versions` | CRUD caller unknown; lib/admin.ts audit helper only | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/content/audit` | `backend/src/content/content.controller.ts#audit` | CRUD caller unknown; lib/admin.ts audit helper only | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | AuditContenuAdmin[] for audit; other responses unknown | content.service.spec.ts; route UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/dashboard/summary` | `backend/src/admin-dashboard/admin-dashboard.controller.ts#summary` | app/admin/page.tsx; frontend/src/lib/admin.ts | aucun Body/Query/Param typé déclaré | `AdminGuard` | AdminDashboardSummary | admin-dashboard.service.spec.ts; app/admin page tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/fraud/flags` | `backend/src/fraud-flags/fraud-flags.controller.ts#lister` | ModerationAdminV3; lib/admin.ts | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | SignalementAdmin[]/DetailSignalementAdmin/SignalementAdmin | fraud-flags.service.spec.ts; ModerationAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/fraud/flags/:id` | `backend/src/fraud-flags/fraud-flags.controller.ts#detail` | ModerationAdminV3; lib/admin.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | SignalementAdmin[]/DetailSignalementAdmin/SignalementAdmin | fraud-flags.service.spec.ts; ModerationAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/fraud/flags/:id` | `backend/src/fraud-flags/fraud-flags.controller.ts#modifier` | ModerationAdminV3; lib/admin.ts | Param id: string; Body dto: UpdateFraudFlagDto [statut:FraudFlagStatus, note:string] | `AdminGuard, PostAuthThrottlerGuard` | SignalementAdmin[]/DetailSignalementAdmin/SignalementAdmin | fraud-flags.service.spec.ts; ModerationAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/lots` | `backend/src/admin-lots/admin-lots.controller.ts#lister` | AdminSectionPage / LotsAdminV3; lib/admin.ts; /admin/lots redirects to shop | aucun Body/Query/Param typé déclaré | `AdminGuard` | client generic LotAdmin[]/LotAdmin; delete typed {id,deleted:true} | admin-lots.service.spec.ts; LotsAdminV3/AdminSectionPage tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/lots` | `backend/src/admin-lots/admin-lots.controller.ts#creer` | AdminSectionPage / LotsAdminV3; lib/admin.ts; /admin/lots redirects to shop | Body dto: CreateAdminLotDto [raffleId:string, nom:string, valeurEstimee:string, quantite:number, fournisseur:string, sponsorId:string, imageUrl:string] | `AdminGuard` | client generic LotAdmin[]/LotAdmin; delete typed {id,deleted:true} | admin-lots.service.spec.ts; LotsAdminV3/AdminSectionPage tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `DELETE /admin/lots/:id` | `backend/src/admin-lots/admin-lots.controller.ts#supprimer` | AdminSectionPage / LotsAdminV3; lib/admin.ts; /admin/lots redirects to shop | Param id: string | `AdminGuard` | client generic LotAdmin[]/LotAdmin; delete typed {id,deleted:true} | admin-lots.service.spec.ts; LotsAdminV3/AdminSectionPage tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/lots/:id` | `backend/src/admin-lots/admin-lots.controller.ts#detail` | AdminSectionPage / LotsAdminV3; lib/admin.ts; /admin/lots redirects to shop | Param id: string | `AdminGuard` | client generic LotAdmin[]/LotAdmin; delete typed {id,deleted:true} | admin-lots.service.spec.ts; LotsAdminV3/AdminSectionPage tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/lots/:id` | `backend/src/admin-lots/admin-lots.controller.ts#modifier` | AdminSectionPage / LotsAdminV3; lib/admin.ts; /admin/lots redirects to shop | Param id: string; Body dto: UpdateAdminLotDto [nom:string, valeurEstimee:string, quantite:number, fournisseur:string, sponsorId:string, imageUrl:string] | `AdminGuard` | client generic LotAdmin[]/LotAdmin; delete typed {id,deleted:true} | admin-lots.service.spec.ts; LotsAdminV3/AdminSectionPage tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/raffles` | `backend/src/raffles/admin-raffles.controller.ts#lister` | RafflesAdminV3; lib/admin.ts | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | TirageAdmin/TirageAdmin[]/ResultatTirageAdmin | raffle-admin-draw.e2e-spec.ts; RafflesAdminV3 tests; US-05/06; §§5.7, 5.9; draw preconditions/audit. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/raffles` | `backend/src/raffles/admin-raffles.controller.ts#creer` | RafflesAdminV3; lib/admin.ts | Body dto: CreateRaffleDto [titre:string, description:string, dateOuverture:string, dateTirage:string, engagementGraine:string, lots:CreateRaffleLotDto[]] | `AdminGuard, PostAuthThrottlerGuard` | TirageAdmin/TirageAdmin[]/ResultatTirageAdmin | raffle-admin-draw.e2e-spec.ts; RafflesAdminV3 tests; US-05/06; §§5.7, 5.9; draw preconditions/audit. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/raffles/:id` | `backend/src/raffles/admin-raffles.controller.ts#modifier` | RafflesAdminV3; lib/admin.ts | Param id: string; Body dto: UpdateRaffleDto [titre:string, description:string, dateTirage:string, lots:CreateRaffleLotDto[]] | `AdminGuard, PostAuthThrottlerGuard` | TirageAdmin/TirageAdmin[]/ResultatTirageAdmin | raffle-admin-draw.e2e-spec.ts; RafflesAdminV3 tests; US-05/06; §§5.7, 5.9; draw preconditions/audit. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/raffles/:id/draw` | `backend/src/raffles/admin-raffles.controller.ts#tirer` | RafflesAdminV3; lib/admin.ts | Param id: string; Body dto: DrawRaffleDto [graineExploitant:string, entropiePublique:string] | `AdminGuard, PostAuthThrottlerGuard` | TirageAdmin/TirageAdmin[]/ResultatTirageAdmin | raffle-admin-draw.e2e-spec.ts; RafflesAdminV3 tests; US-05/06; §§5.7, 5.9; draw preconditions/audit. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/raffles/:id/history` | `backend/src/raffles/admin-raffles.controller.ts#historique` | RafflesAdminV3; lib/admin.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | TirageAdmin/TirageAdmin[]/ResultatTirageAdmin | raffle-admin-draw.e2e-spec.ts; RafflesAdminV3 tests; US-05/06; §§5.7, 5.9; draw preconditions/audit. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/shop/items` | `backend/src/shop/admin-shop.controller.ts#items` | ShopAdminV3; lib/shop.ts | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | {items,total,page,limit} | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/shop/items` | `backend/src/shop/admin-shop.controller.ts#creer` | ShopAdminV3; lib/shop.ts | Body dto: CreateShopItemDto [type:ShopItemType, nom:string, description:string, imageUrl:string, costPoints:number, active:boolean, maxPerUser:number | null, raffleId:string | null] | `AdminGuard, PostAuthThrottlerGuard` | AdminShopItem | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `DELETE /admin/shop/items/:id` | `backend/src/shop/admin-shop.controller.ts#supprimer` | ShopAdminV3; lib/shop.ts | Param id: string | `AdminGuard, PostAuthThrottlerGuard` | void | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/shop/items/:id` | `backend/src/shop/admin-shop.controller.ts#modifier` | ShopAdminV3; lib/shop.ts | Param id: string; Body dto: UpdateShopItemDto [type:ShopItemType, nom:string, description:string, imageUrl:string | null, costPoints:number, active:boolean, maxPerUser:number | null, raffleId:string | null] | `AdminGuard, PostAuthThrottlerGuard` | AdminShopItem | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/shop/items/:id/codes` | `backend/src/shop/admin-shop.controller.ts#importerCodes` | ShopAdminV3; lib/shop.ts | Param id: string; Body dto: ImportShopCodesDto [codes:string[]] | `AdminGuard, PostAuthThrottlerGuard` | ImportShopCodesResponse | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/shop/purchases` | `backend/src/shop/admin-shop.controller.ts#achats` | ShopAdminV3; lib/shop.ts | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | AdminShopPurchasePage | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/sponsors` | `backend/src/sponsors/sponsors.controller.ts#lister` | lib/admin.ts; rendered form caller unknown | aucun Body/Query/Param typé déclaré | `AdminGuard, PostAuthThrottlerGuard` | SponsorAdmin/SponsorAdmin[] | sponsor service specs; UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `POST /admin/sponsors` | `backend/src/sponsors/sponsors.controller.ts#creer` | lib/admin.ts; rendered form caller unknown | Body dto: CreateSponsorDto [nom:string, logoUrl:string] | `AdminGuard, PostAuthThrottlerGuard` | SponsorAdmin/SponsorAdmin[] | sponsor service specs; UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/sponsors/:id` | `backend/src/sponsors/sponsors.controller.ts#modifier` | lib/admin.ts; rendered form caller unknown | Param id: string; Body dto: UpdateSponsorDto [nom:string, logoUrl:string, actif:boolean] | `AdminGuard, PostAuthThrottlerGuard` | SponsorAdmin/SponsorAdmin[] | sponsor service specs; UI test mapping unknown; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/users` | `backend/src/admin-users/admin-users.controller.ts#lister` | UsersAdminV3 / AuditAdminV3; lib/admin.ts; detail/audit callsite unknown | aucun Body/Query/Param typé déclaré | `AdminGuard` | list/status generics found; detail/audit type unknown | admin-users.service.spec.ts; UsersAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/users/:id` | `backend/src/admin-users/admin-users.controller.ts#detail` | UsersAdminV3 / AuditAdminV3; lib/admin.ts; detail/audit callsite unknown | Param id: string | `AdminGuard` | list/status generics found; detail/audit type unknown | admin-users.service.spec.ts; UsersAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /admin/users/:id/audit` | `backend/src/admin-users/admin-users.controller.ts#historique` | UsersAdminV3 / AuditAdminV3; lib/admin.ts; detail/audit callsite unknown | Param id: string | `AdminGuard` | list/status generics found; detail/audit type unknown | admin-users.service.spec.ts; UsersAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /admin/users/:id/status` | `backend/src/admin-users/admin-users.controller.ts#modifierStatut` | UsersAdminV3 / AuditAdminV3; lib/admin.ts; detail/audit callsite unknown | Param id: string; Body dto: UpdateUserStatusDto [actif:boolean] | `AdminGuard` | list/status generics found; detail/audit type unknown | admin-users.service.spec.ts; UsersAdminV3 tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /announcements/active` | `backend/src/announcements/announcements.controller.ts#actives` | CentreNotifications; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `PostAuthThrottlerGuard` | AnnoncePublique[] | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-01/03/06; §§5.1, 5.9. Erreurs métier exactes non établies par cette ligne. |
| `POST /auth/login` | `backend/src/auth/auth.controller.ts#login` | FormulaireAuth / ChangerMotDePasse; frontend/src/lib/auth.ts | Body dto: LoginDto [email:string, motDePasse:string] | `PostAuthThrottlerGuard`; HTTP OK | frontend generic ReponseAuth + cookie | backend/test/auth-lifecycle.e2e-spec.ts; backend/src/auth specs; FormulaireAuth.test.tsx; US-02; §5.2, session/forms/errors. Erreurs métier exactes non établies par cette ligne. |
| `POST /auth/logout` | `backend/src/auth/auth.controller.ts#logout` | FormulaireAuth / ChangerMotDePasse; frontend/src/lib/auth.ts | aucun Body/Query/Param typé déclaré | `OptionalJwtAuthGuard`; HTTP NO_CONTENT | void (204) | backend/test/auth-lifecycle.e2e-spec.ts; backend/src/auth specs; FormulaireAuth.test.tsx; US-02; §5.2, session/forms/errors. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /auth/password` | `backend/src/auth/auth.controller.ts#changerMotDePasse` | FormulaireAuth / ChangerMotDePasse; frontend/src/lib/auth.ts | Body dto: ChangePasswordDto [ancienMotDePasse:string, nouveauMotDePasse:string] | `JwtAuthGuard, PostAuthThrottlerGuard`; HTTP NO_CONTENT | void (204) | backend/test/auth-lifecycle.e2e-spec.ts; backend/src/auth specs; FormulaireAuth.test.tsx; US-02; §5.2, session/forms/errors. Erreurs métier exactes non établies par cette ligne. |
| `POST /auth/register` | `backend/src/auth/auth.controller.ts#register` | FormulaireAuth / ChangerMotDePasse; frontend/src/lib/auth.ts | Body dto: RegisterDto [email:string, motDePasse:string, pseudo:string, accepteReglement:boolean] | `PostAuthThrottlerGuard`; HTTP CREATED | frontend generic ReponseAuth + cookie | backend/test/auth-lifecycle.e2e-spec.ts; backend/src/auth specs; FormulaireAuth.test.tsx; US-02; §5.2, session/forms/errors. Erreurs métier exactes non établies par cette ligne. |
| `GET /auth/session` | `backend/src/auth/auth.controller.ts#session` | FormulaireAuth / ChangerMotDePasse; frontend/src/lib/auth.ts | aucun Body/Query/Param typé déclaré | `OptionalJwtAuthGuard`; HTTP OK | frontend generic ReponseSession | backend/test/auth-lifecycle.e2e-spec.ts; backend/src/auth specs; FormulaireAuth.test.tsx; US-02; §5.2, session/forms/errors. Erreurs métier exactes non établies par cette ligne. |
| `GET /content/:type/:slug` | `backend/src/content/content.controller.ts#public` | exact UI caller unknown | Param type: ManagedContentType; Param slug: string | `aucun explicite; inconnu` | response shape unknown; no matching typed caller | content.service.spec.ts; route UI test mapping unknown; US-01/03/06; §§5.1, 5.9. Erreurs métier exactes non établies par cette ligne. |
| `POST /extension/pair` | `backend/src/extension/extension.controller.ts#apparier` | CodeAppariement; lib/extension.ts; popup via extension/src/commun/endpoints.ts | Body dto: PairDto [code:string] | `PostAuthThrottlerGuard`; HTTP OK | ReponseAppariement | extension-pairing.e2e-spec.ts; service/guard specs; CodeAppariement tests; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `POST /extension/pairing-token` | `backend/src/extension/extension.controller.ts#genererCode` | CodeAppariement; lib/extension.ts; popup via extension/src/commun/endpoints.ts | aucun Body/Query/Param typé déclaré | `JwtAuthGuard, PostAuthThrottlerGuard`; HTTP CREATED | CodeAppariement | extension-pairing.e2e-spec.ts; service/guard specs; CodeAppariement tests; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `GET /extension/pairings` | `backend/src/extension/extension.controller.ts#listerAppareils` | CodeAppariement; lib/extension.ts; popup via extension/src/commun/endpoints.ts | aucun Body/Query/Param typé déclaré | `JwtAuthGuard, PostAuthThrottlerGuard` | ReponseAppareils | extension-pairing.e2e-spec.ts; service/guard specs; CodeAppariement tests; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `DELETE /extension/pairings/:id` | `backend/src/extension/extension.controller.ts#revoquer` | CodeAppariement; lib/extension.ts; popup via extension/src/commun/endpoints.ts | Param id: string | `JwtAuthGuard, PostAuthThrottlerGuard`; HTTP NO_CONTENT | void (204) | extension-pairing.e2e-spec.ts; service/guard specs; CodeAppariement tests; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `GET /health` | `backend/src/app.controller.ts#getHealth` | caller unknown (no direct UI caller found) | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | service return; no server response DTO or frontend type located | app.controller.spec.ts; app.e2e-spec.ts; US-07; §8; isolated healthcheck. Erreurs métier exactes non établies par cette ligne. |
| `GET /me` | `backend/src/me/me.controller.ts#profil` | caller unknown (no direct UI caller found) | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | Profil | me-dashboard-viewer/daily-checkin e2e; me service specs; US-01/07; §§5.1, 8; root/operations behavior. Erreurs métier exactes non établies par cette ligne. |
| `POST /me/daily-checkin` | `backend/src/me/me.controller.ts#checkinQuotidien` | Dashboard/HistoriquePoints/CentreRecompenses; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | service return; server response DTO/client type unknown | me-dashboard-viewer/daily-checkin e2e; me service specs; US-03; §5.3; D-14, day 1 satisfies tier 1, no extra gain. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/dashboard/summary` | `backend/src/me/me.controller.ts#resumeDashboard` | Dashboard/HistoriquePoints/CentreRecompenses; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | ResumeDashboard | me-dashboard-viewer/daily-checkin e2e; me service specs; US-03; §5.3; balance/ledger/streak. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/points/history` | `backend/src/me/me.controller.ts#historiquePoints` | Dashboard/HistoriquePoints/CentreRecompenses; lib/dashboard.ts | Query query: HistoriquePointsDto [page:number, limit:number] | `aucun explicite; inconnu` | HistoriquePoints | me-dashboard-viewer/daily-checkin e2e; me service specs; US-03; §5.3; balance/ledger/streak. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/raffle-tickets` | `backend/src/me/me.controller.ts#mesTicketsTirage` | Dashboard/HistoriquePoints/CentreRecompenses; lib/dashboard.ts | Query query: MesTicketsTirageDto [page:number, limit:number] | `aucun explicite; inconnu` | TicketsTirage | me-dashboard-viewer/daily-checkin e2e; me service specs; US-03; §5.3; balance/ledger/streak. Erreurs métier exactes non établies par cette ligne. |
| `POST /me/raffles/:raffleId/register` | `backend/src/me/me.controller.ts#inscrireTirage` | ListeTirages; lib/dashboard.ts | Param raffleId: string | `aucun explicite; inconnu` | service return; server response DTO/client type unknown | me-dashboard-viewer/daily-checkin e2e; me service specs; US-01/05; §§5.1, 5.7. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/rewards-summary` | `backend/src/me/me.controller.ts#resumeRecompenses` | Dashboard/HistoriquePoints/CentreRecompenses; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | ResumeRecompenses | me-dashboard-viewer/daily-checkin e2e; me service specs; US-03; §5.3; balance/ledger/streak. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/scratch-cards` | `backend/src/scratch-cards/scratch-cards.controller.ts#lister` | CentreRecompenses/ScratchCardModal; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | CarteAGratter[] | scratch-card-no-win.e2e-spec.ts; service specs; CentreRecompenses tests; US-05; §5.6; D-08/D-16. Erreurs métier exactes non établies par cette ligne. |
| `POST /me/scratch-cards/:id/prepare` | `backend/src/scratch-cards/scratch-cards.controller.ts#preparer` | CentreRecompenses/ScratchCardModal; lib/dashboard.ts | Param id: string | `aucun explicite; inconnu` | service return; server response DTO/client type unknown | scratch-card-no-win.e2e-spec.ts; service specs; CentreRecompenses tests; US-05; §5.6; D-08/D-16. Erreurs métier exactes non établies par cette ligne. |
| `POST /me/scratch-cards/:id/scratch` | `backend/src/scratch-cards/scratch-cards.controller.ts#gratter` | CentreRecompenses/ScratchCardModal; lib/dashboard.ts | Param id: string | `aucun explicite; inconnu` | service return; server response DTO/client type unknown | scratch-card-no-win.e2e-spec.ts; service specs; CentreRecompenses tests; US-05; §5.6; D-08/D-16. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/shop/purchases` | `backend/src/shop/me-shop.controller.ts#lister` | BoutiqueViewer; lib/shop.ts | aucun Body/Query/Param typé déclaré | `ViewerGuard, PostAuthThrottlerGuard` | PagePurchases | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-05; §5.8; D-10/D-12. Erreurs métier exactes non établies par cette ligne. |
| `GET /me/shop/purchases/:id/code` | `backend/src/shop/me-shop.controller.ts#code` | BoutiqueViewer; lib/shop.ts | Param id: string | `ViewerGuard, PostAuthThrottlerGuard` | {code:string} | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-05; §5.8; D-10/D-12. Erreurs métier exactes non établies par cette ligne. |
| `GET /public/stats` | `backend/src/app.controller.ts#getPublicStats` | caller unknown (no direct UI caller found) | aucun Body/Query/Param typé déclaré | `aucun explicite; inconnu` | service return; no server response DTO or frontend type located | app.controller.spec.ts; app.e2e-spec.ts; US-01; §5.1; public stats fields. Erreurs métier exactes non établies par cette ligne. |
| `GET /raffles` | `backend/src/raffles/raffles.controller.ts#lister` | ListeTirages; lib/raffles.ts or lib/dashboard.ts; detail/participants helper unknown | aucun Body/Query/Param typé déclaré | `PostAuthThrottlerGuard` | typed clients disagree: Tirage[] vs TiragePublic[]; response unknown until reconciled | raffle controller/service/draw specs; ListeTirages tests; US-01/05; §§5.1, 5.7. Erreurs métier exactes non établies par cette ligne. |
| `GET /raffles/:id` | `backend/src/raffles/raffles.controller.ts#detail` | ListeTirages; lib/raffles.ts or lib/dashboard.ts; detail/participants helper unknown | Param id: string | `PostAuthThrottlerGuard` | detail/participants response unknown; no typed helper matched | raffle controller/service/draw specs; ListeTirages tests; US-01/05; §§5.1, 5.7. Erreurs métier exactes non établies par cette ligne. |
| `GET /raffles/:id/participants` | `backend/src/raffles/raffles.controller.ts#participants` | ListeTirages; lib/raffles.ts or lib/dashboard.ts; detail/participants helper unknown | Param id: string | `PostAuthThrottlerGuard` | detail/participants response unknown; no typed helper matched | raffle controller/service/draw specs; ListeTirages tests; US-01/05; §§5.1, 5.7. Erreurs métier exactes non établies par cette ligne. |
| `GET /raffles/:id/result` | `backend/src/raffles/raffles.controller.ts#resultat` | ListeTirages; lib/raffles.ts or lib/dashboard.ts; detail/participants helper unknown | Param id: string | `PostAuthThrottlerGuard` | ResultatTirage | raffle controller/service/draw specs; ListeTirages tests; US-01/05; §§5.1, 5.7. Erreurs métier exactes non établies par cette ligne. |
| `GET /shop/items` | `backend/src/shop/shop.controller.ts#items` | BoutiqueViewer; lib/shop.ts | aucun Body/Query/Param typé déclaré | `ViewerGuard, PostAuthThrottlerGuard` | PageItems<ShopItem> | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-05; §5.8; D-10/D-12. Erreurs métier exactes non établies par cette ligne. |
| `POST /shop/purchase` | `backend/src/shop/shop.controller.ts#acheter` | BoutiqueViewer; lib/shop.ts | Body dto: PurchaseShopItemDto [itemId:string, idempotencyKey:string] | `ViewerGuard, PostAuthThrottlerGuard` | ShopPurchaseResponse | shop.service.spec.ts; ShopAdminV3/BoutiqueViewer tests; US-05; §5.8; D-10/D-12. Erreurs métier exactes non établies par cette ligne. |
| `GET /streams` | `backend/src/streams/streams.controller.ts#lister` | ListeStreams; lib/streams.ts | aucun Body/Query/Param typé déclaré | `PostAuthThrottlerGuard` | ReponseStreams | streams controller/service specs; ListeStreams tests; US-01/04; §§5.1, 5.4; D-09. Erreurs métier exactes non établies par cette ligne. |
| `PATCH /streams/admin/:id/reward` | `backend/src/streams/streams.controller.ts#mettreAJourRecompense` | ListeStreams; lib/streams.ts | Param id: string; Body dto: UpdateStreamRewardDto [estPartenaire:boolean, bonusPointsHeure:number] | `AdminGuard, PostAuthThrottlerGuard` | service return; no server response DTO or frontend type located | streams controller/service specs; ListeStreams tests; US-06; §5.9; server authorization. Erreurs métier exactes non établies par cette ligne. |
| `GET /viewer/announcements` | `backend/src/announcements/announcements.controller.ts#annoncesViewer` | CentreNotifications; lib/dashboard.ts | aucun Body/Query/Param typé déclaré | `JwtAuthGuard, PostAuthThrottlerGuard` | PageAnnoncesViewer | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-01/03/06; §§5.1, 5.9. Erreurs métier exactes non établies par cette ligne. |
| `POST /viewer/announcements/unread-count` | `backend/src/announcements/announcements.controller.ts#compterAnnoncesNonLuesViewer` | CentreNotifications; lib/dashboard.ts | Body dto: UnreadAnnouncementsCountDto [readIds:string[]] | `JwtAuthGuard, PostAuthThrottlerGuard` | CompteAnnoncesNonLuesViewer | announcements lifecycle/viewer e2e; module specs; AnnouncementsAdminV3 tests; US-01/03/06; §§5.1, 5.9. Erreurs métier exactes non établies par cette ligne. |
| `POST /watch-sessions` | `backend/src/watch-sessions/watch-sessions.controller.ts#ouvrir` | frontend/src/lib/watch-sessions.ts; extension worker via commun/endpoints.ts | Body dto: OuvrirSessionDto [platform:Platform, streamExternalId:string] | `WatchSessionCredentialGuard, PostAuthThrottlerGuard` | SessionVisionnage | watch-session-heartbeat.e2e-spec.ts; service/client specs; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `POST /watch-sessions/:id/close` | `backend/src/watch-sessions/watch-sessions.controller.ts#fermer` | frontend/src/lib/watch-sessions.ts; extension worker via commun/endpoints.ts | Param id: string | `WatchSessionCredentialGuard, PostAuthThrottlerGuard` | SessionVisionnage | watch-session-heartbeat.e2e-spec.ts; service/client specs; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |
| `POST /watch-sessions/:id/heartbeat` | `backend/src/watch-sessions/watch-sessions.controller.ts#heartbeat` | frontend/src/lib/watch-sessions.ts; extension worker via commun/endpoints.ts | Param id: string; Body dto: HeartbeatDto [positionLectureSecondes:number, enLecture:boolean] | `WatchSessionCredentialGuard, PostAuthThrottlerGuard` | ReponseHeartbeat | watch-session-heartbeat.e2e-spec.ts; service/client specs; US-04; §§5.4-5.5; D-03/D-04. Erreurs métier exactes non établies par cette ligne. |

### États Admin, navigateurs, publication et actifs

Les tests frontend présents citent explicitement ces états/actions: chargement
avant réponse, listes vides, pagination début/fin, fallback d’image absente ou
cassée, erreur de chargement récupérable, 403 sur mutation, recherche/filtres,
détail master/detail, formulaire création/modification, publication,
archivage/restauration, import de codes, prérequis de tirage et focus clavier.
Sources: `frontend/src/components/admin/{AdminSectionPage.test.tsx,
AnnouncementsAdminV3.test.tsx,AuditAdminV3.test.tsx,LotsAdminV3.test.tsx,
ModerationAdminV3.test.tsx,RafflesAdminV3.test.tsx,ShopAdminV3.test.tsx,
UsersAdminV3.test.tsx}`. Ce sont des cas testés en source, pas des résultats
d’exécution ni un catalogue complet de chaque champ/erreur DTO.

La documentation V1 `extension/README.md` déclare Chrome uniquement pour
l’extension V1.0; Firefox et Opera sont une intention d’évolution V1.1. Le
manifeste MV3 cible Twitch, YouTube et Kick (domaines www et non-www Kick).
Le runner Chromium avec extension locale n’établit pas une publication Web
Store ni une cohorte d’utilisateurs. OS, versions de navigateurs, package
publié et compatibilité réellement distribuée restent inconnus.

Des usages statiques sont démontrés pour le wordmark dans la navigation, les
images du hero et des étapes marketing, les icônes via `SkkupIcon.tsx`, les
badges Twitch/YouTube/Kick, l’illustration d’extension du dashboard et les
images/masques de scratch cards via `scratch-card-reward.ts`. Des assertions
de chemins/hash existent notamment dans `SkkupIcon.test.tsx`,
`TableauDeBord.test.tsx`, tests de composants i18n et `scratch-card-mask.test.ts`.
Le relevé détaillé des URLs runtime, chemins scratch générés et actifs copiés
au package extension est dans `docs/design/media-inventory.md`. Les fichiers
présents sans usage runtime prouvé y sont distingués. Les dimensions, preuves
de provenance/licence par actif et sélection admissible selon le cahier §4.1
restent à établir. Les captures promotionnelles ne prouvent pas l’inclusion
dans un paquet publié.

Index exhaustif des **44 chemins URL littéraux** repérés par recherche
statique hors fichiers de test (les consommateurs nommés sont les callsites
source):

| Famille | Chemins URL runtime | Callsite principal |
| --- | --- | --- |
| Marque (4) | `/assets/brand/logos/skkup-wordmark-transparent.png`; `/assets/brand/marks/apple-icon.png`; `/assets/brand/marks/skkup-s-favicon.png`; `/assets/brand/search/skkup-favicon.png` | `EnteteVitrine`, `NavigationGlobale`, `AdminSectionPage`, `DashboardSas`, `TableauDeBord`, `AdminSas`, `app/layout.tsx` |
| Dashboard (2) | `/assets/dashboard/illustrations/skkup-icon-extension-dashboard.png`; `/assets/dashboard/rewards/reward-art-sprite-v1.png` | `SkkupIcon.tsx`; `app/globals.css` |
| Icônes UI (29) | `/assets/icons/ui/{analytics,arrow-up-right,arrow,audit,bell,check,chevronDown,close,draws-v2,extension,eye,favorite-heart-active,favorite-heart,flag,flame,gift,megaphone,points,rules,scratchCard,shield,sparkle,status-pending,streams,ticket,timer,trophy,users,warning}.png` | `frontend/src/components/ui/SkkupIcon.tsx` mappe ces icônes; les composants Dashboard/Admin/UI invoquent ce composant. |
| Marketing (6) | `/assets/marketing/backgrounds/vitrine-neon-brick.webp`; `/assets/marketing/hero/skkup-hero-products.png`; `/assets/marketing/steps/skkup-step-install.png`; `/assets/marketing/steps/skkup-step-points-v2.png`; `/assets/marketing/steps/skkup-step-reward.png`; `/assets/marketing/steps/skkup-step-watch.png` | `app/globals.css`, `LocalizedHomeHero.tsx`, `LocalizedHomeSteps.tsx`, `app/layout.tsx` |
| Plateformes (3) | `/assets/platforms/kick.png`; `/assets/platforms/twitch.png`; `/assets/platforms/youtube.png` | `LocalizedDashboardExtensionPage.tsx`, `PlateformeBadge.tsx` |

Les URLs scratch calculées dynamiquement constituent 10 autres chemins servis
par pattern, pas des littéraux `/assets/`: `scratch-tier-{03,07,14,platinum,emerald}.png`
et leurs cinq fichiers `-foil-mask.png`, depuis `frontend/src/lib/scratch-card-reward.ts`.
Le build extension copie aussi `frontend/assets/extension/icons/package/icone-{16,48,128}.png`
vers le package `icones/` et `frontend/assets/extension/brand/skkup-wordmark-transparent.png`
vers `assets/` via `extension/scripts/build.mjs`; ce sont quatre assets de
package sans URL site. Les autres fichiers présents parmi les 72
images sont exclus de ce relevé des usages runtime tant qu’un callsite ou une
copie de build explicite n’a pas été établi.

### Popup, worker et permissions extension

| Surface | Actions ou contrat établis depuis le code | Test présent | Règle / critère V2 et limite |
| --- | --- | --- | --- |
| Popup `extension/src/popup/{popup.html,popup.ts}` | Afficher état associé/non associé, pseudo, plateforme/chaîne, message erreur/succès et progression; changer FR/EN; saisir un code formaté par blocs de 4 (12 caractères); soumettre association; demander état au worker; dissocier l’état local via le worker. | `code-appariement.test.ts`, `progression.test.ts`; tests du worker cités ci-dessous. | Cahier §4.2 et `US-04`; préserver champs, textes, erreurs, progression et states. Tests présents non exécutés; comparaison du popup au package réellement distribué absente. |
| Client `extension/src/commun/endpoints.ts` et `api.ts` | `apparier(code)`; `ouvrirSession`, `envoyerHeartbeat`, `fermerSession`; requête API transporte credential bearer, convertit erreurs HTTP en `ErreurApi` et contrôle les objets réponse. | Tests pairing, cadence/messages et heartbeat côté backend/extension présents. | Cahier §§4.2, 5.4; D-03. Inventaire ci-dessus liste endpoints principaux; schémas complets des réponses et de tous les erreurs HTTP non reproduits champ par champ. |
| Worker `extension/src/arriere-plan/{index.ts,orchestrateur.ts}` | Stocke état/jeton; reçoit état lecture/fin-page; choisit ouverture, heartbeat et clôture; renvoie état au popup; coupe l’état à révocation/auth invalidée; ferme une session après silence de 90 s; localise messages FR/EN. | `orchestrateur.test.ts`, `stockage-jeton.test.ts`, `messages.test.ts`, `cadence.test.ts`. | Cahier §§5.4-5.5; `US-04`; critère: session créditée uniquement par backend, fermeture et révocation cohérentes. Tests non exécutés; package/reconnexion réel non vérifiés. |
| Script de contenu `extension/src/contenu/{index.ts,detecteur-lecture.ts,selection-video.ts,indices-page.ts}` | Interroge la page vidéo toutes les 2 s; observe visibilité/lecture, sélectionne un média et poste état de lecture ou fin de page au worker; les indices site identifient la chaîne/vidéo. | Tests détecteur, sélection, indices et cache présents. | Cahier §5.4; `US-04`. Le contenu observe la page sans token selon README; équivalence des règles d’éligibilité à valider. |
| Manifeste `extension/src/manifeste.ts` et build | MV3; permissions `storage`, `alarms`; origine API seule en `host_permissions`; content matches Twitch, YouTube, Kick et www.kick.com; `document_idle`, `all_frames:false`; popup et service worker; icônes package 16/48/128. | `manifeste.test.ts`, build script source présent; non exécutés. | Cahier §§4.2, 5.4; D-09. V1 README dit Chrome V1.0; aucune preuve Store/versions distribuées ou OS. Aucun `tabs`, `webNavigation`, `history` selon manifeste/README. |

#### Routes et tests source présents par surface

Les 27 routes utilisateur ci-dessus se répartissent en **7 publiques** (`/`,
FAQ, règlement, confidentialité, extension, streams, tirages), **2 auth**,
**10 dashboard** (incluant alias/redirects) et **8 Admin** (incluant `/admin/lots`
qui redirige vers `/admin/shop`); routes/layouts et décisions restent à comparer
à l’appareil V2. `frontend/src/app/assets/[...path]/route.ts` est le 28e handler,
pas une page. Les quatre layouts sont `app/layout.tsx`, `admin/layout.tsx`,
`dashboard/layout.tsx`, `confidentialite/layout.tsx`.

Les **172 fichiers de tests (841 déclarations)** couvrent des niveaux distincts:
backend unitaires/intégration, e2e HTTP, composants React, extension et frontend
e2e. Le nombre de déclarations ne signifie pas qu’un test vérifie chaque route
ou scénario; les fichiers établissent seulement qu’une preuve existe dans
l’arbre. Les modules Admin ont notamment des tests de transitions/formulaires,
états erreur/vide/chargement; chaque DTO et réponse n’a pas une assertion
front-end dédiée repérée. Il n’y a pas eu d’exécution.

### Portée, preuves et inconnues

Cette revue fournit une couverture statique des domaines US-01 à US-07; elle
ne constitue pas une clôture de ces stories ni une preuve de parité. Couvert:
inventaire des routes frontend, 81 actions HTTP des contrôleurs avec leurs
handlers, les callsites trouvés, DTO/champs source, guards explicites, types de
réponse typés côté client et tests nommés; les écrans Admin/actions codés,
états frontend explicitement référencés par les tests, et l’inventaire média
runtime consolidé dans `docs/design/media-inventory.md`. Incomplet ou inconnu:
callers non retrouvés (notamment certains endpoints santé/statistiques,
contenu Admin, sponsors et détails de tirage), payloads de réponse serveur là
où aucun contrat n’est déclaré ou les types client divergent, erreurs métier
et états de chaque formulaire champ par champ, validation complète des
permissions effectives, plateformes/versions réellement publiées, matrice
OS/navigateurs et scénarios opérationnels US-07. Pour les médias, les usages
runtime et fichiers copiés au package sont inventoriés dans
`docs/design/media-inventory.md`; provenance et licences par fichier restent
inconnues, donc aucun actif V1 ne doit être copié avant preuve des droits.
Les tests V1 cités ne sont pas exécutés. Aucun test V2, build, capture,
parcours navigateur ou image-diff n’est une preuve de cette revue. La parité
visuelle demandée au cahier reste à réaliser avant de fermer les portes
correspondantes.

## Dashboard partagé et direction visuelle

### Shell et autorisation approuvés (D-17)

Le propriétaire a approuvé un shell Dashboard unique partagé par Viewer et
Admin, des sections propres aux rôles et une navigation cohérente (D-17). Les
permissions Admin doivent être vérifiées côté serveur. Cette décision fixe le
principe d’architecture/navigation et n’autorise pas à masquer ou accorder des
actions uniquement par l’interface.

### Références et direction visuelle approuvées au cadrage

D-02 demande de préserver le rendu visible de la vitrine et des pages
Connexion/Inscription. Le partage du shell Dashboard est décidé séparément.
Pour le contenu des sections, les références V1 sont `frontend/src/app/dashboard/`
et `frontend/src/app/admin/`, leurs composants réellement appelés et les
endpoints/actions inventoriés plus haut; les parcours par rôle doivent rester
séparés selon autorisation serveur.

Le propriétaire a validé la candidate V1 pour la palette et le langage de
surface bleu nuit, les accents violet/cyan et un glow discret (D-18). Les
tokens V1 correspondants restent la référence de cette direction. Cette
approbation ne fixe pas l’agencement, la densité, les breakpoints V2, les
dimensions des panneaux ou les états détaillés; ces éléments restent à valider
techniquement selon les critères de `docs/design/visual-direction.md`. Les
actifs, usages runtime et sources copiées au package sont inventoriés dans
`docs/design/media-inventory.md`. Leur provenance et licences fichier par
fichier ne sont pas établies; ne copier aucun actif V1 avant preuve des droits.
Aucun rendu V2, capture, contrôle navigateur ou comparaison visuelle V1/V2
n’existe à cette étape. Les revues QA et indépendante PASS portent sur les
critères de cadrage, et non sur un rendu produit. Les validations de layout,
responsive, contrastes et parité devront être exécutées dans les lots concernés.
La palette approuvée ne constitue pas une preuve de rendu ou de parité.

D-17 et D-18 ne modifient pas les décisions de récompenses D-07/D-08 et ne
clôturent pas les validations de rendu, layout/responsive, parité ou audit
du produit V2. La readiness du cadrage demeure `approved`; les validations
visuelles de réalisation restent des préconditions par lot.

Les décisions propriétaire, dont D-17 et D-18, sont consignées dans
`docs/project-management/decision-log.md`. Les chemins V1 cités sont des
références source et non des affirmations de parité déjà obtenue dans V2. La
relecture indépendante du cadrage est PASS; la comparaison visuelle exécutée
sur des écrans V2 reste à faire quand ces écrans existeront. Les inconnues
techniques et de déploiement sont affectées aux lots concernés, sans révoquer
l’approbation du cadrage.

## Décision

Le cadrage de conception est `approved` au 2026-11-16, après inventaire
statique V1 et arbitrages applicables D-14 à D-16, revue QA de la direction
D-17/D-18, audit indépendant et scan des marqueurs. Il autorise la planification
des lots et leur implémentation sous leurs préconditions spécifiques; il
n’autorise aucune bascule de production, migration, publication ou copie
d’actif sans les preuves et décisions énumérées plus haut.

Résultats au cadrage, 2026-11-16 : Produit PASS sur l’inventaire et les
arbitrages D-14 à D-16; QA PASS sur la direction Dashboard D-17/D-18; Auditeur
PASS indépendant; scan des marqueurs PASS. Aucun test V2, build, parcours
navigateur, comparaison visuelle, mesure responsive/contraste ou test négatif
d’accès Admin n’est déclaré exécuté.
