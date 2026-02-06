import bpy
import glob
import sys
sys.path.append("S:\Programming\Python Scripts\Blender-mis-import")
import ImportMis
class RunImportMis:
        filesList = glob.glob(str("S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\lbmissions_pq")+"\*.mcs", recursive=False)
        for filepath in filesList:      
            ImportMis.load(bpy.types.Operator, bpy.context, filepath)
        print("hi im python and im VERY Stupid")