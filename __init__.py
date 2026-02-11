
if "bpy" in locals():
    import importlib

    if "import_mis" in locals():
        importlib.reload(import_mis)

import bpy
from bpy.props import (BoolProperty,
                       StringProperty)

from bpy_extras.io_utils import (ImportHelper)

bl_info = {
    "name": "Import mis",
    "author": "MBCollector672",
    "description": "mis/mcs (Marble Blast mission file) importer for Blender",
    "blender": (4,5,0),
    "version": (1,0,0),
    "location": "File > Import-Export",
    "category": "Import-Export",

}

class ImportMis:
    bl_idname = "import_scene.mis"
    bl_label = "Import Marble Blast .mis"
    bl_options = {"REGISTER", "UNDO"}

    filter_glob: StringProperty(
    default="*.mis",
    options={"HIDDEN"},
    )

    include_dif: BoolProperty(
    name="Include DIF",
    description="Include DIF models, which include interiors and moving platforms"
    default=True,
    )

    include_dts: BoolProperty(
    name="Include DTS",
    description="Include DTS models, which include items, scenery, and other similar non-interior objects",
    default=True,
    )

    include_static_interiors: BoolProperty(
    name="Include Static Interiors",
    description="Include interiors that do not move"
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
    description="Tries to import only the highest level of detail for DTS files. Very inconsistent at the moment"
    default=True,
    )

    recalculate_dts_normals: BoolProperty(
    name="Recalculate DTS Normals",
    description="Recalculate DTS normals. This can fix DTS objects having messed up shading on import",
    default=True,
    )

    use_mbu_pads: BoolProperty(
    name="Use MBU Pads",
    description="Use MBU pads when importing MBU levels. By default, these levels will import MBM pads and MBP checkpoints."
    default=True,
    )

    # dts import configs
    reference_keyframe: BoolProperty(
    name="DTS Import: Reference Keyframes"
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

        keywords = self.as_keywords(ignore=("filter_glob", "split_mode"))
        return import_mis.load(self, context, **keywords)
    
class ImportMcs:
    bl_idname = "import_scene.mcs"
    bl_label = "Import PlatinumQuest .mcs"
    bl_options = {"REGISTER", "UNDO"}

    filter_glob: StringProperty(
    default="*.mcs",
    options={"HIDDEN"},
    )

    include_dif: BoolProperty(
    name="Include DIF",
    description="Include DIF models, which include interiors and moving platforms"
    default=True,
    )

    include_dts: BoolProperty(
    name="Include DTS",
    description="Include DTS models, which include items, scenery, and other similar non-interior objects",
    default=True,
    )

    include_static_interiors: BoolProperty(
    name="Include Static Interiors",
    description="Include interiors that do not move"
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
    description="Tries to import only the highest level of detail for DTS files. Very inconsistent at the moment"
    default=True,
    )

    recalculate_dts_normals: BoolProperty(
    name="Recalculate DTS Normals",
    description="Recalculate DTS normals. This can fix DTS objects having messed up shading on import",
    default=True,
    )

    use_mbu_pads: BoolProperty(
    name="Use MBU Pads",
    description="Use MBU pads when importing MBU levels. By default, these levels will import MBM pads and MBP checkpoints."
    default=True,
    )

    # dts import configs
    reference_keyframe: BoolProperty(
    name="DTS Import: Reference Keyframes"
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

        keywords = self.as_keywords(ignore=("filter_glob", "split_mode"))
        return import_mis.load(self, context, **keywords)
    
def menu_func_import_mis(self, context):
    self.layout.operator(ImportMis.bl_idname, text="Marble Blast (.mis)")

def menu_func_import_mcs(self, context):
    self.layout.operator(ImportMcs.bl_idname, text="PlatinumQuest (.mcs)")

def register():
    bpy.utils.register_class(ImportMis)
    bpy.utils.register_class(ImportMcs)
    bpy.types.TOPBAR_MT_FILE_import.append(menu_func_import_mis)
    bpy.types.TOPBAR_MT_FILE_import.append(menu_func_import_mcs)

def unregister():
    bpy.utils.unregister_class(ImportMis)
    bpy.utils.unregister_class(ImportMcs)
    bpy.types.TOPBAR_MT_FILE_import.remove(menu_func_import_mis)
    bpy.types.TOPBAR_MT_FILE_import.remove(menu_func_import_mcs)
    
if __name__ == "__main__":
    register()