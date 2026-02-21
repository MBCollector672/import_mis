# Import Mis

Blender plugin to import Marble Blast .mis files and PlatinumQuest .mcs files.
Requires [io_dif](https://github.com/RandomityGuy/io_dif) and [io_scene_dts](https://github.com/MBCollector672/io_scene_dts) installed in Blender to function properly.

## Note
Import Mis has mostly been tested using PlatinumQuest. It should work correctly on Marble Blast Gold as well but I can't guarantee compatibility with other mods (if you find incompatibilities, let me know).
It also cannot import from compiled scripts and heavily relies on .mcs and .cs files to be uncompiled to function properly. If you want to import a .mcs file, you should import from a local copy of the [PQ development repository](https://github.com/The-New-Platinum-Team/PlatinumQuest-Dev).
You can link this copy in addon preferences and import_mis will import from there if an object doesn't exist in the correct location relative to the mission file.

## Features

### Interior importing

- Powered by [io_dif](https://github.com/RandomityGuy/io_dif)
- Imports all interiors and aligns/scales/rotates them the way they are set up in-game
- Can fix PathedInterior (moving platform) positions if they are positioned differently in the .dif than the .mis

### Shape importing

- Powered by [io_scene_dts](https://github.com/MBCollector672/io_scene_dts)
- Imports all shapes and aligns/scales/rotates them the way they are set up in-game
- Can fix shapes importing without textures
- Can fix shapes importing without transparency
- Can fix shapes importing with messed-up normals
- Can automatically apply smooth shading to DTS files so they look like they do in-game
- Tries to delete collision automatically to make the DTS look like it does in-game
- Fixes weird transparency behavior that occurs on a couple of DTS models (gems, the MBG finish sign)

### Gem randomization

Highly configurable gem import settings, including:
- Option to randomize gems that use the default skin (GemItem)
- Option to disable platinum gems for non-PlatinumQuest gems, meaning MBG/MBU levels can easily not include platinum gems (which is not a vanilla MBG/MBU behavior)
- Option to disable "Illegal" MBU gems (colors that are not red, yellow, or blue)

## Installation

Download the plugin from releases and install it as you would any other Blender plugin. Make sure you have [io_dif](https://github.com/RandomityGuy/io_dif) and [io_scene_dts](https://github.com/MBCollector672/io_scene_dts) installed.

## Known issues/limitations

- Untested on Mac/Linux
- Very likely to fail if the mission file has items that are placed with code
- A few uncommon DTS files do not import correctly
- pack1marble.dts and pack2marble.dts freeze the DTS importer (no idea why, they import fine using io_scene_dts from Blender)
- DTS LODs are usually not correctly deleted
- Some DTS collision is not deleted
- Cannot import IFL animated textures
- Cannot recreate the Marble Blast behavior of darkening/lightning the texture depending on scaling
- Slows down the more files you have previously imported (this appears to be an issue with io_scene_dts and maybe io_dif, so there isn't anything I can do about this unfortunately)
- Can take a long time on very large levels (like Citadel)
- Cannot import from compiled scripts (ex. .mcs.dso, .cs.dso)
- Somewhat hacky as MB is often inconsistent in how its files are organized

## Credits

Thanks RandomityGuy for io_dif and for making a few edits to io_scene_dts to fix older DTS versions not importing.
Thanks to everyone who has contributed to io_scene_dts over the years including SimplyEpic5, BansheeRubber, port, irrelevant.irreverent, and Eagle517.
