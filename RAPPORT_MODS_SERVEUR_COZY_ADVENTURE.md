# Audit des mods serveur — Cozy Adventure

Manifeste audité : `cozy_mods_source.json` (142 mods), NeoForge 1.21.1.

## Légende

- **REQUIS** : à installer sur le serveur pour garder le contenu, la génération, les mécaniques ou une dépendance nécessaire.
- **OPTIONNEL** : fonctionne ou apporte un bénéfice côté serveur, mais son absence ne retire pas le contenu essentiel du modpack.
- **INUTILE** : mod strictement client (rendu, HUD, sons, animations, shaders, contrôles) ; ne pas le mettre sur un serveur dédié.

> « Requis » signifie requis pour héberger **ce modpack complet**, pas nécessairement requis pour permettre à un client de se connecter à un serveur vanilla.

## Résultat complet

| # | Mod (ID du manifeste) | Verdict serveur | Motif court |
|---:|---|---|---|
| 1 | `accessories` | **REQUIS** | API et emplacements d’accessoires utilisés par le contenu. |
| 2 | `adorablehamsterpets` | **REQUIS** | Ajoute des entités, objets et mécaniques de familiers. |
| 3 | `ambientsounds` | **INUTILE** | Ambiance sonore calculée uniquement par le client. |
| 4 | `amendments` | **REQUIS** | Modifie le comportement de blocs vanilla et synchronise ces mécaniques. |
| 5 | `appleskin` | **OPTIONNEL** | Principalement HUD client ; présence serveur seulement utile à certaines infos de saturation. |
| 6 | `architectury` | **REQUIS** | Bibliothèque nécessaire à des mods de contenu du pack. |
| 7 | `mr_armor_standarms` | **REQUIS** | Datapack/mod de gameplay appliqué par le serveur. |
| 8 | `awesomedungeonocean` | **REQUIS** | Génération de structures océaniques. |
| 9 | `backpacked` | **REQUIS** | Ajoute sacs, inventaires et données persistantes. |
| 10 | `backpackedwoc` | **REQUIS** | Extension de contenu de Backpacked. |
| 11 | `beautify` | **REQUIS** | Ajoute des blocs et objets décoratifs. |
| 12 | `betteradvancements` | **INUTILE** | Refonte uniquement l’écran des progrès. |
| 13 | `betterf3` | **INUTILE** | Remplace uniquement le HUD F3 du client. |
| 14 | `big_lost_city` | **REQUIS** | Génération de structure. |
| 15 | `bookshelfinspector` | **REQUIS** | Ajoute une interaction/inspection synchronisée des bibliothèques. |
| 16 | `brewinandchewin` | **REQUIS** | Ajoute blocs, recettes, aliments et mécaniques. |
| 17 | `cavedust` | **INUTILE** | Effets visuels de poussière dans les grottes. |
| 18 | `chefsdelight` | **REQUIS** | Ajoute des villageois et du contenu Farmer’s Delight. |
| 19 | `chunky` | **OPTIONNEL** | Outil serveur de prégénération des chunks. |
| 20 | `citresewn` | **INUTILE** | Textures d’objets personnalisées côté client. |
| 21 | `citresewn_neopatcher` | **INUTILE** | Correctif client pour CIT Resewn. |
| 22 | `cloth_config` | **OPTIONNEL** | Bibliothèque de configuration ; inutile seule, requise seulement par un mod serveur qui la déclare. |
| 23 | `clumps` | **OPTIONNEL** | Optimisation serveur des orbes d’expérience. |
| 24 | `cluttered` | **REQUIS** | Ajoute meubles, blocs et objets. |
| 25 | `cnb` | **REQUIS** | Creatures and Beasts ajoute des entités et du gameplay. |
| 26 | `commonnetworking` | **REQUIS** | Bibliothèque réseau nécessaire à des mods communs du pack. |
| 27 | `connectiblechains` | **REQUIS** | Ajoute des connexions de chaînes avec état synchronisé. |
| 28 | `connector` | **REQUIS** | Nécessaire sur le serveur pour charger les mods Fabric du pack qui y sont requis. |
| 29 | `continuity` | **INUTILE** | Textures connectées, rendu uniquement client. |
| 30 | `cozyhome` | **REQUIS** | Ajoute du contenu décoratif/blocs. |
| 31 | `creativecore` | **INUTILE** | Dans ce pack, sert au mod client AmbientSounds ; pas nécessaire au serveur. |
| 32 | `crittersandcompanions` | **REQUIS** | Ajoute créatures, objets et comportements. |
| 33 | `cropsloverain` | **REQUIS** | Modifie la croissance des cultures côté serveur. |
| 34 | `curios` | **REQUIS** | API d’équipement utilisée par des objets du pack. |
| 35 | `cubes_without_borders` | **INUTILE** | Gestion de fenêtre plein écran sans bordure. |
| 36 | `delightlib` | **REQUIS** | Bibliothèque des extensions Farmer’s Delight présentes. |
| 37 | `detailab` | **INUTILE** | Affichage détaillé de la barre d’armure. |
| 38 | `diagonalfences` | **REQUIS** | Modifie formes/connexions de blocs. |
| 39 | `diagonalwalls` | **REQUIS** | Modifie formes/connexions de blocs. |
| 40 | `diagonalwindows` | **REQUIS** | Modifie formes/connexions de blocs. |
| 41 | `displaydelight` | **REQUIS** | Ajoute des blocs d’exposition et leurs données. |
| 42 | `mr_dungeons_andtaverns` | **REQUIS** | Génération de structures ; client non nécessaire, serveur indispensable. |
| 43 | `dynamic_fps` | **INUTILE** | Réduit les FPS/ressources quand le client est en arrière-plan. |
| 44 | `easyanvils` | **REQUIS** | Modifie la mécanique et l’interface logique des enclumes. |
| 45 | `easymagic` | **REQUIS** | Modifie la mécanique des tables d’enchantement. |
| 46 | `eatinganimation` | **INUTILE** | Animation visuelle de consommation. |
| 47 | `enhancedcats` | **REQUIS** | Ajoute/modifie variantes et données des chats. |
| 48 | `entity_model_features` | **INUTILE** | Modèles d’entités personnalisés côté client. |
| 49 | `entity_texture_features` | **INUTILE** | Textures d’entités personnalisées côté client. |
| 50 | `entityculling` | **INUTILE** | Optimisation du rendu client. |
| 51 | `mr_epic_structuresjungletemples` | **REQUIS** | Génération de structures ; client non nécessaire. |
| 52 | `euphoria_patcher` | **INUTILE** | Correctifs/variantes pour shaders côté client. |
| 53 | `expandeddelight` | **REQUIS** | Ajoute aliments, recettes, cultures et blocs. |
| 54 | `fairylights` | **REQUIS** | Ajoute blocs/entités décoratives synchronisées. |
| 55 | `farmersdelight` | **REQUIS** | Mod de contenu et de gameplay central. |
| 56 | `fastitemframes` | **REQUIS** | Remplace/optimise le fonctionnement des cadres côté serveur aussi. |
| 57 | `ferritecore` | **OPTIONNEL** | Optimisation mémoire utile sur serveur, sans contenu. |
| 58 | `fabric_api` | **REQUIS** | Forgified Fabric API, dépendance des mods Fabric chargés via Connector. |
| 59 | `fps_overlay` | **INUTILE** | Compteur de FPS client. |
| 60 | `framework` | **REQUIS** | Bibliothèque de MrCrayfish requise par Backpacked/Refurbished Furniture. |
| 61 | `fwa` | **INUTILE** | Animations visuelles de blocs côté client. |
| 62 | `fzzy_config` | **REQUIS** | Bibliothèque déclarée par un mod commun du pack. |
| 63 | `geckolib` | **REQUIS** | Bibliothèque d’animation requise par plusieurs mods de créatures/contenu. |
| 64 | `ghosts` | **REQUIS** | Ajoute des entités et mécaniques de fantômes. |
| 65 | `gml` | **REQUIS** | Chargeur de langage nécessaire au mod Groovy `ghosts`. |
| 66 | `horseman` | **REQUIS** | Modifie les chevaux et leurs interactions. |
| 67 | `iceberg` | **REQUIS** | Bibliothèque requise par des mods installés des deux côtés. |
| 68 | `immediatelyfast` | **INUTILE** | Optimisation du rendu immédiat client. |
| 69 | `ipo` | **REQUIS** | Génération des avant-postes de pillards. |
| 70 | `invmove` | **INUTILE** | Contrôles client dans les inventaires. |
| 71 | `iris` | **INUTILE** | Chargeur de shaders client. |
| 72 | `item_interactions_mod` | **INUTILE** | Animations/présentation d’interactions d’objets côté client. |
| 73 | `jade` | **OPTIONNEL** | Overlay client ; serveur facultatif pour fournir des données plus complètes. |
| 74 | `justzoom` | **INUTILE** | Zoom caméra client. |
| 75 | `kiwi` | **REQUIS** | Bibliothèque nécessaire à des mods de contenu, notamment Snow! Real Magic!. |
| 76 | `konkrete` | **INUTILE** | Dans ce pack, bibliothèque de mods d’interface client. |
| 77 | `koopascritters` | **REQUIS** | Ajoute des créatures et leur gameplay. |
| 78 | `kotlinforforge` | **REQUIS** | Runtime Kotlin requis par des mods communs du pack. |
| 79 | `legendarytooltips` | **INUTILE** | Apparence des infobulles côté client. |
| 80 | `beachparty` | **REQUIS** | Ajoute blocs, objets, recettes et mécaniques. |
| 81 | `libraryferret` | **REQUIS** | Bibliothèque requise par un ou plusieurs mods de contenu. |
| 82 | `lithium` | **OPTIONNEL** | Optimisation de logique très utile au serveur, sans contenu. |
| 83 | `lootbeams` | **INUTILE** | Faisceaux visuels au-dessus des objets au sol. |
| 84 | `mcwfurnitures` | **REQUIS** | Ajoute meubles, blocs et recettes. |
| 85 | `monolib` | **REQUIS** | Bibliothèque nécessaire à des mods de contenu. |
| 86 | `moogs_structures` | **REQUIS** | Bibliothèque de génération des structures de Moog. |
| 87 | `mmr` | **REQUIS** | Génération de mineshafts réimaginés. |
| 88 | `moonlight` | **REQUIS** | Bibliothèque requise par Supplementaries/Amendments et autres contenus. |
| 89 | `moredelight` | **REQUIS** | Ajoute contenu et recettes Farmer’s Delight. |
| 90 | `mousetweaks` | **INUTILE** | Contrôles souris d’inventaire côté client. |
| 91 | `mythicalcritters` | **REQUIS** | Ajoute des créatures et du gameplay. |
| 92 | `naturalist` | **REQUIS** | Ajoute animaux, comportements et objets. |
| 93 | `nightlights` | **REQUIS** | Ajoute des blocs lumineux. |
| 94 | `nirvana_lib` | **REQUIS** | Bibliothèque nécessaire à un mod de contenu du pack. |
| 95 | `noisium` | **OPTIONNEL** | Optimisation serveur de la génération du monde ; aucun contenu ajouté. |
| 96 | `notenoughanimations` | **INUTILE** | Animations de joueur en troisième personne côté client. |
| 97 | `oceansdelight` | **REQUIS** | Ajoute aliments, recettes et objets. |
| 98 | `octolib` | **REQUIS** | Bibliothèque nécessaire à des mods communs du pack. |
| 99 | `owo` | **REQUIS** | Bibliothèque requise par des mods Fabric communs. |
| 100 | `particlerain` | **INUTILE** | Effets de pluie/neige en particules côté client. |
| 101 | `particular` | **INUTILE** | Effets visuels et particules d’ambiance côté client. |
| 102 | `patchouli` | **REQUIS** | Bibliothèque/livres de documentation requis par du contenu du pack. |
| 103 | `pickupnotifier` | **INUTILE** | Notification visuelle de ramassage côté client ; serveur facultatif non utile ici. |
| 104 | `plushables` | **REQUIS** | Ajoute blocs/objets peluches. |
| 105 | `polytone` | **INUTILE** | Personnalisation de couleurs/sons par resource pack côté client. |
| 106 | `prism` | **INUTILE** | Ici il s’agit de Prism Library pour Legendary Tooltips, uniquement client. |
| 107 | `puddleflood` | **REQUIS** | Les flaques sont visibles côté client, mais leur création/état de monde demande le serveur pour l’expérience complète. |
| 108 | `punchy` | **INUTILE** | Traitement visuel/couleurs côté client. |
| 109 | `puzzleslib` | **REQUIS** | Bibliothèque des mods Fuzs installés côté serveur (Easy Anvils, etc.). |
| 110 | `refurbished_furniture` | **REQUIS** | Ajoute meubles, blocs, inventaires et recettes. |
| 111 | `ribbits` | **REQUIS** | Ajoute grenouilles, villages et mécaniques. |
| 112 | `scalablelux` | **OPTIONNEL** | Optimisation du moteur de lumière côté serveur. |
| 113 | `serene_shrubbery` | **REQUIS** | Ajoute végétation/blocs et génération. |
| 114 | `shulkerboxtooltip` | **INUTILE** | Aperçu d’inventaire dans l’infobulle client. |
| 115 | `simplehats` | **REQUIS** | Ajoute objets de chapeaux et données d’équipement. |
| 116 | `skinlayers3d` | **INUTILE** | Rendu 3D des skins côté client. |
| 117 | `smoothgui` | **INUTILE** | Animation/lissage des interfaces client. |
| 118 | `smoothswapping` | **INUTILE** | Animation visuelle des déplacements d’objets en inventaire. |
| 119 | `snowrealmagic` | **REQUIS** | Modifie les couches de neige et leurs interactions côté serveur. |
| 120 | `sodium` | **INUTILE** | Moteur de rendu client. |
| 121 | `softimprints` | **INUTILE** | Empreintes visuelles dans la neige côté client. |
| 122 | `sound_physics_remastered` | **INUTILE** | Simulation acoustique locale côté client. |
| 123 | `statuseffectbars` | **INUTILE** | Affichage des durées d’effets côté client. |
| 124 | `streamsreflowing` | **REQUIS** | Modifie la génération/le comportement des cours d’eau. |
| 125 | `subtle_effects` | **INUTILE** | Effets visuels et sonores client ; support serveur facultatif non nécessaire. |
| 126 | `supplementaries` | **REQUIS** | Ajoute blocs, objets, automatisations et mécaniques. |
| 127 | `swinginglanterns` | **INUTILE** | Animation visuelle des lanternes côté client. |
| 128 | `tellus` | **REQUIS** | Génération de terrain/données géographiques côté serveur. |
| 129 | `toomanypaintings` | **REQUIS** | Ajoute des variantes/contenus de tableaux synchronisés. |
| 130 | `visualworkbench` | **REQUIS** | Établis persistants avec inventaire/état côté serveur. |
| 131 | `wakes` | **INUTILE** | Cette build charge `ClientLevel` et échoue sur un serveur dédié ; à conserver uniquement sur les clients. |
| 132 | `leans_extra_backpacks` | **REQUIS** | Extension de contenu de Backpacked. |
| 133 | `whaleborne` | **REQUIS** | Ajoute entité, objets et mécanique de navire. |
| 134 | `xaerominimap` | **INUTILE** | Minicarte client ; module serveur facultatif non nécessaire au fonctionnement. |
| 135 | `xaeroworldmap` | **INUTILE** | Carte du monde côté client. |
| 136 | `yet_another_config_lib_v3` | **REQUIS** | Dépendance de Critters and Companions ; son API est référencée par un mixin commun sur serveur dédié. |
| 137 | `yungsapi` | **REQUIS** | Bibliothèque indispensable aux structures YUNG installées. |
| 138 | `betterdeserttemples` | **REQUIS** | Génération de structures côté serveur. |
| 139 | `betteroceanmonuments` | **REQUIS** | Génération de structures côté serveur. |
| 140 | `betterstrongholds` | **REQUIS** | Génération de structures côté serveur. |
| 141 | `yungsbridges` | **REQUIS** | Génération de structures côté serveur. |
| 142 | `yungsextras` | **REQUIS** | Génération de structures côté serveur. |

## Listes directement exploitables

### À installer sur le serveur (requis)

`accessories`, `adorablehamsterpets`, `amendments`, `architectury`, `mr_armor_standarms`, `awesomedungeonocean`, `backpacked`, `backpackedwoc`, `beautify`, `big_lost_city`, `bookshelfinspector`, `brewinandchewin`, `chefsdelight`, `cluttered`, `cnb`, `commonnetworking`, `connectiblechains`, `connector`, `cozyhome`, `crittersandcompanions`, `cropsloverain`, `curios`, `delightlib`, `diagonalfences`, `diagonalwalls`, `diagonalwindows`, `displaydelight`, `mr_dungeons_andtaverns`, `easyanvils`, `easymagic`, `enhancedcats`, `mr_epic_structuresjungletemples`, `expandeddelight`, `fairylights`, `farmersdelight`, `fastitemframes`, `fabric_api`, `framework`, `fzzy_config`, `geckolib`, `ghosts`, `gml`, `horseman`, `iceberg`, `ipo`, `koopascritters`, `kotlinforforge`, `beachparty`, `libraryferret`, `mcwfurnitures`, `monolib`, `moogs_structures`, `mmr`, `moonlight`, `moredelight`, `mythicalcritters`, `naturalist`, `nightlights`, `nirvana_lib`, `oceansdelight`, `octolib`, `owo`, `patchouli`, `plushables`, `puddleflood`, `puzzleslib`, `refurbished_furniture`, `ribbits`, `serene_shrubbery`, `simplehats`, `snowrealmagic`, `streamsreflowing`, `supplementaries`, `tellus`, `toomanypaintings`, `visualworkbench`, `leans_extra_backpacks`, `whaleborne`, `yet_another_config_lib_v3`, `yungsapi`, `betterdeserttemples`, `betteroceanmonuments`, `betterstrongholds`, `yungsbridges`, `yungsextras`.

### Facultatifs mais utiles au serveur

`appleskin`, `chunky`, `cloth_config`, `clumps`, `ferritecore`, `jade`, `lithium`, `noisium`, `scalablelux`.

### À retirer du serveur (client-only)

`ambientsounds`, `betteradvancements`, `betterf3`, `cavedust`, `citresewn`, `citresewn_neopatcher`, `continuity`, `creativecore`, `cubes_without_borders`, `detailab`, `dynamic_fps`, `eatinganimation`, `entity_model_features`, `entity_texture_features`, `entityculling`, `euphoria_patcher`, `fps_overlay`, `fwa`, `immediatelyfast`, `invmove`, `iris`, `item_interactions_mod`, `justzoom`, `konkrete`, `legendarytooltips`, `lootbeams`, `mousetweaks`, `notenoughanimations`, `particlerain`, `particular`, `pickupnotifier`, `polytone`, `prism`, `punchy`, `shulkerboxtooltip`, `skinlayers3d`, `smoothgui`, `smoothswapping`, `sodium`, `softimprints`, `sound_physics_remastered`, `statuseffectbars`, `subtle_effects`, `swinginglanterns`, `wakes`, `xaerominimap`, `xaeroworldmap`.

## Points d’attention

- Les mods de génération de structures doivent être présents **avant de générer les chunks**. Les ajouter ensuite ne régénère pas les zones déjà explorées.
- Conserve ensemble `connector` et `fabric_api` côté serveur : plusieurs mods requis du pack sont des mods Fabric exécutés sous NeoForge par Connector.
- Une bibliothèque classée « inutile » l’est selon les dépendances présentes dans ce manifeste. Si tu ajoutes plus tard un mod serveur qui en dépend, son statut peut changer.
- Pour la stabilité, garde exactement les mêmes versions des mods de contenu sur le serveur et les clients.
