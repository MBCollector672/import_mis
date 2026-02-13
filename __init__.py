# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
if "bpy" in locals():
    import importlib

    if "import_mis" in locals():
        importlib.reload(__package__)

import bpy
import os
import json
from pathlib import Path
from bpy.props import (BoolProperty,
                       StringProperty)

from bpy_extras.io_utils import (ImportHelper)

def readprefs():
    user_prefs_path = bpy.utils.extension_path_user("bl_ext.user_default.MBCollector672_import_mis", path="")
    if os.path.exists(os.path.join(user_prefs_path, "prefs.json")):
        with open(os.path.join(user_prefs_path, "prefs.json"), "r") as prefs_file:
            prefs = json.load(prefs_file)
    else:
        prefs = {"PQ_dev_dir": ""}
    return prefs



def writeprefs(cls: "ImportMisPreferences", context: bpy.types.Context):
    prefs = {"PQ_dev_dir": cls.PQ_dev_dir}
    user_prefs_path = bpy.utils.extension_path_user("bl_ext.user_default.MBCollector672_import_mis",path="")
    if not os.path.exists(user_prefs_path):
        bpy.utils.extension_path_user("bl_ext.user_default.MBCollector672_import_mis",path="",create=True)
    if not os.path.exists(os.path.join(user_prefs_path, "prefs.json")):
        prefs_file = open(os.path.join(user_prefs_path, "prefs.json"), "w")
        prefs_file.close()
    with open(os.path.join(user_prefs_path, "prefs.json"), "w") as prefs_file:
        json.dump(prefs, prefs_file)
    


class ImportMisPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    prefs = readprefs()

    PQ_dev_dir: StringProperty(
        name="PlatinumQuest Development Directory",
        description="The path to your local copy of PlatinumQuest's development repository",
        subtype='DIR_PATH',
        update=writeprefs,
        default=prefs.get('PQ_dev_dir')
    )

    def returnpref(pref):
        prefs = readprefs()
        return prefs.get(pref)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Import Mis Preferences")
        layout.prop(self, "PQ_dev_dir")
    

class ImportMis(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.mis"
    bl_label = "Import Marble Blast .mis"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".mis"
    filter_glob: StringProperty(
    default="*.mis",
    options={"HIDDEN"},
    )

    include_dif: BoolProperty(
    name="Include DIF",
    description="Include DIF models, which include interiors and moving platforms",
    default=True,
    )

    include_dts: BoolProperty(
    name="Include DTS",
    description="Include DTS models, which include items, scenery, and other similar non-interior objects",
    default=True,
    )

    include_static_interiors: BoolProperty(
    name="Include Static Interiors",
    description="Include interiors that do not move",
    default=True,
    )

    include_pathed_interiors: BoolProperty(
    name="Include Pathed Interiors",
    description="Include moving platforms",
    default=True,
    )

    include_path_triggers: BoolProperty(
    name="Include Path Triggers",
    description="Import the path triggers of moving platforms",
    default=True,
    )

    include_game_entities: BoolProperty(
    name="Include Game Entities",
    description="Include game entities, which are empties sometimes included in dif files that define where in-game objects go",
    default=False,
    )

    get_pathed_interiors_from_mis: BoolProperty(
    name="Get Pathed Interiors From Mis",
    description="Defines moving platform placement based on the mission file rather than the dif they're embedded into. Useful if platforms are positioned incorrectly",
    default=True,
    )

    get_pathed_interior_by_name: BoolProperty(
    name="Get Pathed Interior By Name",
    description="Set moving platform positions by the name of their interior. If turned off, importing will slow down considerably",
    default=True,
    )

    include_item: BoolProperty(
    name="Include Items",
    description="Include items, such as gems, powerups, etc.",
    default=True,
    )

    include_static_shape: BoolProperty(
    name="Include Static Shapes",
    description="Include static shapes like scenery and hazards",
    default=True,
    )

    include_tsstatic: BoolProperty(
    name="Include TSStatics",
    description="Include TSStatic objects, which are effectively raw DTS files with no code attached to them",
    default=True,
    )

    include_path_nodes: BoolProperty(
    name="Include Path Nodes",
    description="Include the path nodes used by the camera in PQ level previews in the files to import",
    default=False,
    )

    attempt_to_fix_transparency: BoolProperty(
    name="Attempt to Fix Transparency",
    description="If a DTS is supposed to be transparent, try to set it to transparent automatically",
    default=True,
    )

    random_gems: BoolProperty(
    name="Random Gems",
    description="If a gem is the default GemItem which would be given a random skin upon mission load, give it a random skin on import",
    default=True,
    )

    allow_illegal_mbu_gems: BoolProperty(
    name="Allow Illegal MBU Gems",
    description="Allow gem randomization to color MBU gems colors other than red, yellow, and blue",
    default=False,
    )

    allow_platinum_gems: BoolProperty(
    name="Allow Non-PQ Platinum Gems",
    description="Allow gem randomization to set MBU and MBG gems to platinum. Should be enabled if importing an MBP .mis",
    default=False,
    )

    delete_dts_col: BoolProperty(
    name="Delete DTS Collision",
    description="Tries to delete DTS collision, which looks ugly in Blender. Usually works, but not always",
    default=True,
    )

    try_only_highest_lod: BoolProperty(
    name="Only Highest LOD",
    description="Tries to import only the highest level of detail for DTS files. Very inconsistent at the moment",
    default=True,
    )

    recalculate_dts_normals: BoolProperty(
    name="Recalculate DTS Normals",
    description="Recalculate DTS normals. This can fix DTS objects having messed up shading on import",
    default=True,
    )

    use_mbu_pads: BoolProperty(
    name="Use MBU Pads",
    description="Use MBU pads when importing MBU levels. By default, these levels will import MBM pads and MBP checkpoints.",
    default=True,
    )

    # dts import configs
    reference_keyframe: BoolProperty(
    name="DTS Import: Reference Keyframes",
    description="Reference animation stored in the DTS file. Can mess up moving DTS files around.",
    default=False,
    )

    import_sequences: BoolProperty(
    name="DTS Import: Import Sequences",
    description="Automatically add keyframes for embedded sequences",
    default=False,
    )

    use_armature: BoolProperty(
    name="DTS Import: Use Armature",
    description="Import bones into an armature instead of empties. Does not work with 'Import sequences'",
    default=False,
    )

    def execute(self,context):
        from . import import_mis

        PQ_dev_dir = ImportMisPreferences.returnpref("PQ_dev_dir")
        keywords = self.as_keywords(ignore=("filter_glob", "split_mode"))
        return import_mis.load(self, context, PQ_dev_dir, **keywords)
    
class ImportMcs(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.mcs"
    bl_label = "Import PlatinumQuest .mcs"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".mcs"
    filter_glob: StringProperty(
    default="*.mcs",
    options={"HIDDEN"},
    )

    include_dif: BoolProperty(
    name="Include DIF",
    description="Include DIF models, which include interiors and moving platforms",
    default=True,
    )

    include_dts: BoolProperty(
    name="Include DTS",
    description="Include DTS models, which include items, scenery, and other similar non-interior objects",
    default=True,
    )

    include_static_interiors: BoolProperty(
    name="Include Static Interiors",
    description="Include interiors that do not move",
    default=True,
    )

    include_pathed_interiors: BoolProperty(
    name="Include Pathed Interiors",
    description="Include moving platforms",
    default=True,
    )

    include_path_triggers: BoolProperty(
    name="Include Path Triggers",
    description="Import the path triggers of moving platforms",
    default=True,
    )

    include_game_entities: BoolProperty(
    name="Include Game Entities",
    description="Include game entities, which are empties sometimes included in dif files that define where in-game objects go",
    default=False,
    )

    get_pathed_interiors_from_mis: BoolProperty(
    name="Get Pathed Interiors From Mis",
    description="Defines moving platform placement based on the mission file rather than the dif they're embedded into. Useful if platforms are positioned incorrectly",
    default=True,
    )

    get_pathed_interior_by_name: BoolProperty(
    name="Get Pathed Interior By Name",
    description="Set moving platform positions by the name of their interior. If turned off, importing will slow down considerably",
    default=True,
    )

    include_item: BoolProperty(
    name="Include Items",
    description="Include items, such as gems, powerups, etc.",
    default=True,
    )

    include_static_shape: BoolProperty(
    name="Include Static Shapes",
    description="Include static shapes like scenery and hazards",
    default=True,
    )

    include_tsstatic: BoolProperty(
    name="Include TSStatics",
    description="Include TSStatic objects, which are effectively raw DTS files with no code attached to them",
    default=True,
    )

    include_path_nodes: BoolProperty(
    name="Include Path Nodes",
    description="Include the path nodes used by the camera in PQ level previews in the files to import",
    default=False,
    )

    attempt_to_fix_transparency: BoolProperty(
    name="Attempt to Fix Transparency",
    description="If a DTS is supposed to be transparent, try to set it to transparent automatically",
    default=True,
    )

    random_gems: BoolProperty(
    name="Random Gems",
    description="If a gem is the default GemItem which would be given a random skin upon mission load, give it a random skin on import",
    default=True,
    )

    allow_illegal_mbu_gems: BoolProperty(
    name="Allow Illegal MBU Gems",
    description="Allow gem randomization to color MBU gems colors other than red, yellow, and blue",
    default=False,
    )

    allow_platinum_gems: BoolProperty(
    name="Allow Non-PQ Platinum Gems",
    description="Allow gem randomization to set MBU and MBG gems to platinum. Should be enabled if importing an MBP .mis",
    default=False,
    )

    delete_dts_col: BoolProperty(
    name="Delete DTS Collision",
    description="Tries to delete DTS collision, which looks ugly in Blender. Usually works, but not always",
    default=True,
    )

    try_only_highest_lod: BoolProperty(
    name="Only Highest LOD",
    description="Tries to import only the highest level of detail for DTS files. Very inconsistent at the moment",
    default=True,
    )

    recalculate_dts_normals: BoolProperty(
    name="Recalculate DTS Normals",
    description="Recalculate DTS normals. This can fix DTS objects having messed up shading on import",
    default=True,
    )

    use_mbu_pads: BoolProperty(
    name="Use MBU Pads",
    description="Use MBU pads when importing MBU levels. By default, these levels will import MBM pads and MBP checkpoints.",
    default=True,
    )

    # dts import configs
    reference_keyframe: BoolProperty(
    name="DTS Import: Reference Keyframes",
    description="Reference animation stored in the DTS file. Can mess up moving DTS files around.",
    default=False,
    )

    import_sequences: BoolProperty(
    name="DTS Import: Import Sequences",
    description="Automatically add keyframes for embedded sequences",
    default=False,
    )

    use_armature: BoolProperty(
    name="DTS Import: Use Armature",
    description="Import bones into an armature instead of empties. Does not work with 'Import sequences'",
    default=False,
    )

    def execute(self,context):
        from . import import_mis

        PQ_dev_dir = ImportMisPreferences.returnpref("PQ_dev_dir")
        keywords = self.as_keywords(ignore=("filter_glob", "split_mode"))
        return import_mis.load(self, context, PQ_dev_dir, **keywords)
    
def menu_func_import_mis(self, context):
    self.layout.operator(ImportMis.bl_idname, text="Marble Blast (.mis)")

def menu_func_import_mcs(self, context):
    self.layout.operator(ImportMcs.bl_idname, text="PlatinumQuest (.mcs)")

def register():
    bpy.utils.register_class(ImportMis)
    bpy.utils.register_class(ImportMcs)
    bpy.utils.register_class(ImportMisPreferences)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mis)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mcs)

def unregister():
    bpy.utils.unregister_class(ImportMis)
    bpy.utils.unregister_class(ImportMcs)
    bpy.utils.unregister_class(ImportMisPreferences)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_mis)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_mcs)
    
if __name__ == "__main__":
    register()