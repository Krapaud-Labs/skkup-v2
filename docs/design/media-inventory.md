# Inventaire des médias

## État

Aucun actif V1 n'est copié ni retenu dans le dépôt V2. L'inventaire statique des usages du commit accepté est consigné ci-dessous; la provenance et les droits individuels ne sont pas établis, donc aucun actif n'est autorisé à copier par cette revue. Le visuel de barème fourni est une source documentaire, pas un actif produit à intégrer.

## Référence et méthode

Source: `Krapaud-Labs/Skkup@fcc4767f3ece9efc069d1a1c413942067cb89c93`, consultée par lecture des objets Git. Le checkout V1 voisin était dirty et n'a pas été modifié. Les URL sont reliées au chemin source servi par le route handler Next; les médias à chemin dynamique sont reliés au générateur de récompenses; les copies extension sont reliées au script de build. Les octets ne sont pas extraits vers le projet V2.

SHA-256 recalculé sur les octets récupérés depuis chaque blob V1 avec `git cat-file blob <commit>:<path>` et SHA-256 standard. Reproduction possible pour un fichier avec `git -C ../Skkup cat-file blob <commit>:<path> | shasum -a 256`. Les dimensions et formats sont lus depuis les en-têtes PNG/WebP. Les callsites viennent des références statiques de `frontend/assets/README.md`, `frontend/src/app/assets/[...path]/route.ts`, `frontend/src/components/ui/SkkupIcon.tsx`, `frontend/src/lib/scratch-card-reward.ts` et `extension/scripts/build.mjs`. La présence d'un callsite prouve une référence source, pas un rendu navigateur ou une inclusion dans une distribution publiée. La table couvre 44 URL littérales, 10 chemins scratch dynamiques et 4 fichiers copiés au build de l'extension.

## Manifeste des médias runtime V1

La provenance/licence de chaque ligne est notée `Non documentée`: les commentaires de catégorie dans le README V1 ne permettent pas de rattacher une autorisation ou une licence précise à chaque blob.

| Chemin source exact V1 | Usage statique | Octets | Format et dimensions | SHA-256 | Provenance/licence |
| --- | --- | ---: | --- | --- | --- |
| `frontend/assets/brand/logos/skkup-wordmark-transparent.png` | URL /assets/brand/logos/skkup-wordmark-transparent.png | 1230978 | PNG 2072x759 | `be96ff6a4a57dc34ea4462589e6b47d683ff18e84ca8881244ec9cae340dd718` | Non documentée |
| `frontend/assets/brand/marks/apple-icon.png` | URL /assets/brand/marks/apple-icon.png | 1758886 | PNG 1254x1254 | `d66c2d8f7b607c84c8e69f3e63d9be69183701eb7efb918f9e049f78a8bf58e0` | Non documentée |
| `frontend/assets/brand/marks/skkup-s-favicon.png` | URL /assets/brand/marks/skkup-s-favicon.png | 1758886 | PNG 1254x1254 | `d66c2d8f7b607c84c8e69f3e63d9be69183701eb7efb918f9e049f78a8bf58e0` | Non documentée |
| `frontend/assets/brand/search/skkup-favicon.png` | URL /assets/brand/search/skkup-favicon.png | 1758886 | PNG 1254x1254 | `d66c2d8f7b607c84c8e69f3e63d9be69183701eb7efb918f9e049f78a8bf58e0` | Non documentée |
| `frontend/assets/dashboard/illustrations/skkup-icon-extension-dashboard.png` | URL /assets/dashboard/illustrations/skkup-icon-extension-dashboard.png | 1421807 | PNG 1254x1254 | `98b65edbb21e9b59f0e9d2823b7ff850079e7006e75c2d1376f56e6865f30167` | Non documentée |
| `frontend/assets/dashboard/rewards/reward-art-sprite-v1.png` | URL /assets/dashboard/rewards/reward-art-sprite-v1.png | 1009705 | PNG 768x768 | `881425e5732b77973ae98363c6eff5182368e5e06172f2c95c0a62058ba8685b` | Non documentée |
| `frontend/assets/icons/ui/analytics.png` | URL /assets/icons/ui/analytics.png | 843752 | PNG 1254x1254 | `3424bc77e11736c8fae6344969604d6f17eb83e9bf702b030179bb5914806dad` | Non documentée |
| `frontend/assets/icons/ui/arrow-up-right.png` | URL /assets/icons/ui/arrow-up-right.png | 933126 | PNG 1254x1254 | `8ee9973a5e32f70c30e80b2ef0aa7b57f44b73804f589e450bec18010d1c4b36` | Non documentée |
| `frontend/assets/icons/ui/arrow.png` | URL /assets/icons/ui/arrow.png | 682229 | PNG 1254x1254 | `c4f231d02f7496bea2b7cb0c053f7261d2b3862dc1b82ffa4fdae09b0afd78a7` | Non documentée |
| `frontend/assets/icons/ui/audit.png` | URL /assets/icons/ui/audit.png | 913581 | PNG 1254x1254 | `8e9c9780776f1b3482380c5f843926285c1797ec7a8775acf0d08e79c9842c42` | Non documentée |
| `frontend/assets/icons/ui/bell.png` | URL /assets/icons/ui/bell.png | 781335 | PNG 1254x1254 | `9add245a46f427afb8b766dbc0b3de5a4865dd74a77632ff4536fa37c9a98a2d` | Non documentée |
| `frontend/assets/icons/ui/check.png` | URL /assets/icons/ui/check.png | 712920 | PNG 1254x1254 | `572732e19d279828274d8cba350e610cbebcf167e56c8dc924f437c6f980aea6` | Non documentée |
| `frontend/assets/icons/ui/chevronDown.png` | URL /assets/icons/ui/chevronDown.png | 747535 | PNG 1254x1254 | `ed28850a412e6b4412e36cb5b3283baa90edc94a70672fcf576428d9633a676a` | Non documentée |
| `frontend/assets/icons/ui/close.png` | URL /assets/icons/ui/close.png | 842666 | PNG 1254x1254 | `4f31463740e5912042e669ab74dc5787c424584189692293216bd24809a7b586` | Non documentée |
| `frontend/assets/icons/ui/draws-v2.png` | URL /assets/icons/ui/draws-v2.png | 626707 | PNG 1254x1254 | `64195caefcd5313c75042bee44b84837a9e56ca8d451cbeb01d72d71c3d80991` | Non documentée |
| `frontend/assets/icons/ui/extension.png` | URL /assets/icons/ui/extension.png | 891194 | PNG 1254x1254 | `c7e64fc77fa022af91dd3039cc0bcad4328a66446757bef40a830c4bbcfba66e` | Non documentée |
| `frontend/assets/icons/ui/eye.png` | URL /assets/icons/ui/eye.png | 839709 | PNG 1254x1254 | `f35369f781f15b0c3704302e56750d9fce44a6e8043f252dc568da6e9b68fc61` | Non documentée |
| `frontend/assets/icons/ui/favorite-heart-active.png` | URL /assets/icons/ui/favorite-heart-active.png | 750901 | PNG 1254x1254 | `02153ab4481a54bc8219e6fa98361d1c6f45f2d7d08017fc722173604f878cb9` | Non documentée |
| `frontend/assets/icons/ui/favorite-heart.png` | URL /assets/icons/ui/favorite-heart.png | 982348 | PNG 1254x1254 | `583c9aae390c7f5931dc2b435c2429d03c5c2f259760d34391a69af413528251` | Non documentée |
| `frontend/assets/icons/ui/flag.png` | URL /assets/icons/ui/flag.png | 838928 | PNG 1254x1254 | `8f4a32f17d1ffba4bb1d30c922380f82d6cd0f0cf73c387ef762259b1b129a78` | Non documentée |
| `frontend/assets/icons/ui/flame.png` | URL /assets/icons/ui/flame.png | 791400 | PNG 1254x1254 | `b1fe4c389dc1253df85b292f81deedb8b67f108bbb98a74b4ae72af960360865` | Non documentée |
| `frontend/assets/icons/ui/gift.png` | URL /assets/icons/ui/gift.png | 953461 | PNG 1254x1254 | `4aca3e63fe9d83adb7c5c812c3c443b7559d1a021e57c5963ad53b0f3404b982` | Non documentée |
| `frontend/assets/icons/ui/megaphone.png` | URL /assets/icons/ui/megaphone.png | 886551 | PNG 1254x1254 | `71e7a7b9fc6ea32a6efc88db736070069b941e13d2f8153f2fc88d11e765d33a` | Non documentée |
| `frontend/assets/icons/ui/points.png` | URL /assets/icons/ui/points.png | 1110702 | PNG 1254x1254 | `00b2ef947e70b77659f8c5282b5a384fe6e9d815e52735b740e23d20c28670cb` | Non documentée |
| `frontend/assets/icons/ui/rules.png` | URL /assets/icons/ui/rules.png | 919100 | PNG 1254x1254 | `c899013e3db10c11f772264bb93c0eb8e691c8ab61c1f4b622015602d476fb8f` | Non documentée |
| `frontend/assets/icons/ui/scratchCard.png` | URL /assets/icons/ui/scratchCard.png | 920618 | PNG 1254x1254 | `52f0b199cfb048bfee9a61c90e2d423febe076b90b31ba16ed4d531cbc6e53f8` | Non documentée |
| `frontend/assets/icons/ui/shield.png` | URL /assets/icons/ui/shield.png | 861950 | PNG 1254x1254 | `274de3de33d2d6d5fb93150490594e760233dde1eb65ed46883efb67a6216d9e` | Non documentée |
| `frontend/assets/icons/ui/sparkle.png` | URL /assets/icons/ui/sparkle.png | 743790 | PNG 1254x1254 | `7bf15b6368ab512a4d1938565cb2579f9871c4303060ca742e5b47f792adcbdd` | Non documentée |
| `frontend/assets/icons/ui/status-pending.png` | URL /assets/icons/ui/status-pending.png | 1216582 | PNG 1254x1254 | `7d2bf3a47006387f1003ac714bab1ce0b09c7527164a6979148d47ad263ced7e` | Non documentée |
| `frontend/assets/icons/ui/streams.png` | URL /assets/icons/ui/streams.png | 915798 | PNG 1254x1254 | `8b43b8f577a03b76e5151cb795149fa6d1d5050643e72aa9ad6954bc6ebbcf69` | Non documentée |
| `frontend/assets/icons/ui/ticket.png` | URL /assets/icons/ui/ticket.png | 848406 | PNG 1254x1254 | `86d8d0bb818943c69c6ad31eb15f252f45eb8ebe74f7bb969a221f018ea96316` | Non documentée |
| `frontend/assets/icons/ui/timer.png` | URL /assets/icons/ui/timer.png | 963377 | PNG 1254x1254 | `225472eb7939e0b3d8f073aa28d1408a135441822d41e8806e75a07559ca71bc` | Non documentée |
| `frontend/assets/icons/ui/trophy.png` | URL /assets/icons/ui/trophy.png | 1039618 | PNG 1254x1254 | `e3abea269c9c4cfb211814d4150e3791ab413159eac64930d794e975a2fa3e8c` | Non documentée |
| `frontend/assets/icons/ui/users.png` | URL /assets/icons/ui/users.png | 882507 | PNG 1254x1254 | `9d983cf43d38e0f5e8ecb6564a50896324724e500545c3c589e7532fac56e8c3` | Non documentée |
| `frontend/assets/icons/ui/warning.png` | URL /assets/icons/ui/warning.png | 799198 | PNG 1254x1254 | `b5b071a1b29b3cc33a0ee3f219cc064df02a9816891d51d85ed97fa92c8d3dca` | Non documentée |
| `frontend/public/assets/marketing/backgrounds/vitrine-neon-brick.webp` | URL /assets/marketing/backgrounds/vitrine-neon-brick.webp | 273924 | WEBP 1672x941 | `5b01c7e4f2fcdfca2eae0d56f4b62ea325db1a407439c972564d7c16391cb7d4` | Non documentée |
| `frontend/assets/marketing/hero/skkup-hero-products.png` | URL /assets/marketing/hero/skkup-hero-products.png | 2296424 | PNG 1536x1024 | `2ab69281297d97aa83c87eb340b84eabc52d6d7a36c491e96efc31e74f289267` | Non documentée |
| `frontend/assets/marketing/steps/skkup-step-install.png` | URL /assets/marketing/steps/skkup-step-install.png | 1923163 | PNG 1585x992 | `4e668a3de7d251fb6dde4cb653d3b9164f157157485ac651815f6d7e17928fdd` | Non documentée |
| `frontend/assets/marketing/steps/skkup-step-points-v2.png` | URL /assets/marketing/steps/skkup-step-points-v2.png | 1923981 | PNG 1584x993 | `82ac0ae036c5b675c462d6aa71ccabb6580bf17942fd3427fcaec1d50f5db288` | Non documentée |
| `frontend/assets/marketing/steps/skkup-step-reward.png` | URL /assets/marketing/steps/skkup-step-reward.png | 1950942 | PNG 1585x992 | `862d5d2561ef4e8f7bf54bb8de3109dc5823cc8ec8594751ff10286cb95b5f3b` | Non documentée |
| `frontend/assets/marketing/steps/skkup-step-watch.png` | URL /assets/marketing/steps/skkup-step-watch.png | 1996839 | PNG 1585x992 | `75412ec457ce42bad1d0493bdc3a307b4e40597b88989c6205f23a284d4ee197` | Non documentée |
| `frontend/assets/platforms/kick.png` | URL /assets/platforms/kick.png | 11862 | PNG 1363x1533 | `45bfc9211dcc72b740ea2c32ed49a4f46ef7c816dc00eacaae18d0ae83944f9a` | Non documentée |
| `frontend/assets/platforms/twitch.png` | URL /assets/platforms/twitch.png | 1746 | PNG 128x128 | `d77bfb3e036f4852718780fafeffdc30ed16fd293b50789d81cf7d109a28741b` | Non documentée |
| `frontend/assets/platforms/youtube.png` | URL /assets/platforms/youtube.png | 2284 | PNG 128x128 | `d5f400eb1c511ae5925ccbe5e488d9c51055b89624ffdf712ac263cd2e45691e` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-03.png` | pattern scratch-card-reward.ts | 2385639 | PNG 1671x941 | `d3955e0c3a89f3dcbc2fd514c66011126a766376df32277ac6b047e6ce4f0c61` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-03-foil-mask.png` | pattern scratch-card-reward.ts | 7837 | PNG 1671x941 | `6856cb30cd5117f3cfd33dd1fa4c4aa1a50ef6adacda47211f35d912da7b8181` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-07.png` | pattern scratch-card-reward.ts | 2756790 | PNG 1671x941 | `39896037458fc0405b578c3fb40879bed6b5cb3bd448ee66d261eec54a481486` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-07-foil-mask.png` | pattern scratch-card-reward.ts | 8087 | PNG 1671x941 | `923471d7716df35e095abec72ae7c942a4f15321b63b1b707abc75d1bbc6bf53` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-14.png` | pattern scratch-card-reward.ts | 2542915 | PNG 1672x941 | `64276960aa065dd230c9bcc8210d184221201e7baf5e414799ba50716817281e` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-14-foil-mask.png` | pattern scratch-card-reward.ts | 7828 | PNG 1672x941 | `4b031ce257bccc7b6d6af1f98b5fd57ad32202762b88a52de81951452c8df5d7` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-platinum.png` | pattern scratch-card-reward.ts | 2798265 | PNG 1672x941 | `af846f7089e2f0bd576248ea126633de9a359af8b4fa47db9dbb9b59a31db320` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-platinum-foil-mask.png` | pattern scratch-card-reward.ts | 7880 | PNG 1672x941 | `c6748e812200837d6f9516b94201cae837c23a2b1db3eea767cce1b75b753c4d` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-emerald.png` | pattern scratch-card-reward.ts | 2510709 | PNG 1672x941 | `f56e784545d2de116a3852d1debce701bb501d4e88ba53a9a95f6be0ef0cd9b2` | Non documentée |
| `frontend/assets/dashboard/rewards/scratch-tier-emerald-foil-mask.png` | pattern scratch-card-reward.ts | 8035 | PNG 1672x941 | `0658b2f2112dc19787d3aec12bb990aa21c0b4cc6b06067e4901d9a9570290f2` | Non documentée |
| `frontend/assets/extension/brand/skkup-wordmark-transparent.png` | copied by extension/scripts/build.mjs | 77517 | PNG 300x110 | `0e0c331b394eb77e10213b8dfe9c71c88336097fcb01ff6a99e05f1b15c8ba37` | Non documentée |
| `frontend/assets/extension/icons/package/icone-16.png` | copied by extension/scripts/build.mjs | 1002 | PNG 16x16 | `c8ea75e75b3036deb8260fe966650b4a77b0d532ca31db60d84722d0658aba27` | Non documentée |
| `frontend/assets/extension/icons/package/icone-48.png` | copied by extension/scripts/build.mjs | 6761 | PNG 48x48 | `b28d329790ef7592845593279bd70f1ff1e2b09ffc373fb196f14959055b0932` | Non documentée |
| `frontend/assets/extension/icons/package/icone-128.png` | copied by extension/scripts/build.mjs | 41689 | PNG 128x128 | `d64b9f0e3469a156e28afd6ae37a24912c957609cb0b023b8c913f05cda887ae` | Non documentée |

## Correspondance des callsites

- Wordmark: `frontend/src/components/navigation/{EnteteVitrine.tsx,NavigationGlobale.tsx}`, `frontend/src/components/admin/AdminSectionPage.tsx` et `frontend/src/components/dashboard/DashboardSas.tsx`.
- Icônes du navigateur: `frontend/src/app/layout.tsx`; monogramme de l'Admin et du Viewer: `frontend/src/app/admin/page.tsx`, `frontend/src/components/admin/AdminSas.tsx` et `frontend/src/components/dashboard/TableauDeBord.tsx`.
- Les 29 pictogrammes UI sont mappés par `frontend/src/components/ui/SkkupIcon.tsx`; les écrans Admin/Viewer les invoquent par identifiant. Le route handler `frontend/src/app/assets/[...path]/route.ts` liste les sources servies.
- Illustration d'extension: `frontend/src/components/i18n/LocalizedDashboardExtensionPage.tsx`; sprite de récompenses: `frontend/src/app/globals.css` (`.skuup-scratch-art`, `.skuup-rewards-selected-art`).
- Fond de vitrine: `frontend/src/app/globals.css`; hero: `frontend/src/components/i18n/LocalizedHomeHero.tsx`; quatre visuels d'étapes: `frontend/src/components/i18n/LocalizedHomeSteps.tsx`.
- Logos Twitch, YouTube et Kick: `frontend/src/components/i18n/LocalizedDashboardExtensionPage.tsx`; Twitch et YouTube sont aussi mappés par `frontend/src/components/streams/PlateformeBadge.tsx`.
- Scratch cards: chemins nommés par `frontend/src/lib/scratch-card-reward.ts`; wordmark et trois icônes package sont copiés par `extension/scripts/build.mjs`.

Les trois PNG de marque `apple-icon.png`, `skkup-s-favicon.png` et `skkup-favicon.png` ont la même taille, les mêmes dimensions et la même SHA-256 dans ce commit. Leur identité binaire ne prouve pas qu'un chemin soit redondant; aucun chemin n'est supprimé sur cette base.

## Actifs disponibles sans usage runtime établi

Le commit V1 contient 72 fichiers image sous `frontend/assets/` et `frontend/public/assets/`. Les 58 lignes ci-dessus couvrent les URL runtime littérales, chemins scratch générés et sources copiées au package extension. Les fichiers restants ou sources/visuels promotionnels/documentaires sont exclus tant qu'un callsite runtime ou une copie de build n'est pas prouvé. Leur provenance et leurs droits ne sont pas hérités des autres lignes.

## Règle avant toute copie dans V2

Avant de copier un actif, faire valider son usage et ses droits fichier par fichier, conserver ce chemin source et cette SHA-256 comme provenance, comparer l'actif choisi au rendu de référence et mettre à jour ce manifeste avec la destination V2. Ne pas réutiliser un média seulement parce qu'il existe dans l'arbre V1.
