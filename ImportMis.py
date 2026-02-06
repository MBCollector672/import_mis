import bpy
import os
import sys
import math
import glob
import random
import operator
import concurrent.futures
from pathlib import Path
# import io_dif
ioDifPath = bpy.utils.user_resource('SCRIPTS', path="addons")
sys.path.append(ioDifPath)
import io_dif
from io_dif import import_dif
import io_scene_dts
from io_scene_dts import import_dts    

def load(operator, context, filepath,
     # mis import configs
    include_path_triggers = False,
    include_path_nodes = False,
    include_static_interiors = True,
    include_pathed_interiors = True,
    include_game_entities = False,
    include_dts = True,
    include_dif = True,
    include_item = True,
    include_tsstatic = True,
    include_static_shape = True,
    attempt_to_fix_transparency = True,
    random_gems = True,
    allowIllegalMbuGems = False,
    allowPlatinumGems = False,
    deleteDtsCol = True,
    onlyHighestLod = True,
    # dts import configs
    reference_keyframe = False,
    import_sequences = False,
    use_armature = False,
    debug_report = False
    ):
    failedDif = []
    failedDts = []
    def material_check(texNode,mat,matOldName,item,bsdfNode,attempt_to_fix_transparency,onlyTransparency = False):
        fileExtensions = ["",".png",".jpg",".PNG",".JPG"]
        if texNode == None and onlyTransparency == False:
            texNode = mat.node_tree.nodes.new("ShaderNodeTexImage")
            matOldName = matOldName[:matOldName.find("#")] if matOldName.find("#") != -1 else matOldName
            imagePath = (str(Path(item["file"]).parent) + "\\" + matOldName)
            print(imagePath)
            if item["skin"] != "base" and item["skin"] != None:
                newImagePath = str(imagePath).replace("base",str(item["skin"]))
            else:
                newImagePath = imagePath
            if item["skin"] != None:
                print(item["skin"])
                try: texNode.image = bpy.data.images.load(newImagePath)
                except:
                    print("Skin",item["skin"],"at",newImagePath,"doesn't seem to exist. Using base skin instead")
                    texNode.image = bpy.data.images.load(imagePath)
                bpy.data.materials[mat.name].node_tree.links.new(texNode.outputs["Color"], bsdfNode.inputs["Base Color"])
            else:
                # trash hacky fix for materials sometimes not having their file extension in the name
                for fileExtension in fileExtensions:
                    try: 
                        texNode.image = bpy.data.images.load(imagePath + fileExtension)
                        break
                    except: 
                        if fileExtensions.index(fileExtension) == len(fileExtensions) - 1:
                            print("No image found at " + imagePath)
                            nodes.remove(texNode)
                            texNode = ""
                if texNode != "":
                    bpy.data.materials[mat.name].node_tree.links.new(texNode.outputs["Color"], bsdfNode.inputs["Base Color"])
                    print("used image is" + str(texNode.image))
        if texNode != "" and item["gem"] == True and texNode.image.name.find("gemshine") == -1:
            bpy.data.images[texNode.image.name].alpha_mode = 'NONE'
        if texNode != "" and mat.torque_props.use_transparency == True and attempt_to_fix_transparency == True:
            bpy.data.materials[mat.name].node_tree.links.new(texNode.outputs["Alpha"], bsdfNode.inputs["Alpha"])

    def find_in_file(misString, string, scriptString, activeMisDataPath, rand, allowIllegalMbuGems, allowPlatinumGems):

        mbgValidGems = ["red", "yellow", "blue", "base", "purple", "green", "turquoise", "orange", "black"]
        mbuValidGems = ["red", "yellow", "blue"]
        mbuIllegalGems = ["base", "purple", "green", "turquoise", "orange", "black", "white"]
        pqValidGems = ["red", "yellow", "blue", "base", "purple", "green", "turquoise", "orange", "black", "platinum"]
        def get_next_quote(misString, index):
            return misString.find("\"", index)
        
        def get_gem_item(dataBlock, rand):
            # change gem lists depending on settings
            mbuValidGems.extend(mbuIllegalGems) if allowIllegalMbuGems == True else None
            mbuValidGems.append("platinum") if allowPlatinumGems == True else None
            mbgValidGems.append("platinum") if allowPlatinumGems == True else None
            newDataBlock = None
            game = None
            # find the gem's type (game) and color (skin)
            if dataBlock.find("Fancy") != -1:
                color = str.casefold(dataBlock[12:])
            else:
                color = str.casefold(dataBlock[7:])
            if color != "":
                if (color.find("pq") != -1 or color.find("mbu") != -1):
                    colorNameList = color.split("_")
                    if len(colorNameList[0]) >= 3:
                        color = colorNameList[0]
                    else:
                        color = "base"
                    if dataBlock.find("Fancy") == -1:
                        game = colorNameList[1] 
                    else: 
                        game = "fancy"
                else:
                    game = "mbg"
                    color = "base" if len(color) < 3 else color
            else:
                game = "mbg"
                color = "base" if len(color) < 3 else color
            match game:
                case "mbg":
                    newDataBlock = "GemItem"
                    if rand == True and color == "base":
                        color = str(mbgValidGems[random.randint(0,len(mbgValidGems) - 1)])
                case "mbu":
                    newDataBlock = "GemItem_MBU"
                    if rand == True and color == "base":
                        color = str(mbuValidGems[random.randint(0,len(mbuValidGems) - 1)])
                case "pq":
                    newDataBlock = "GemItem_PQ"
                    if rand == True and color == "base":
                        color = str(pqValidGems[random.randint(0,len(pqValidGems) - 1)])
                case "fancy":
                    newDataBlock = "FancyGemItem_PQ"
                    if rand == True and color == "base":
                        color = str(pqValidGems[random.randint(0,len(pqValidGems) - 1)])
                case _:
                    print("Failed to determine gem color. This should never happen.")
            return(newDataBlock,color)


        
        itemIndex = misString.find(string)
        objList = []
        # run misString.find last so its value is checked before the while loop runs again
        while(itemIndex != -1):
            # indexes of all the values we need to store and use in blender
            isGem = False
            dtsSkin = None
            itemPositionIndex = misString.find("position", itemIndex)
            itemRotationIndex = misString.find("rotation", itemIndex)
            itemScaleIndex = misString.find("scale", itemIndex)
            dtsSkinIndex = misString.find("skin", itemIndex)
            if string == "TSStatic(":
                itemFileIndex = misString.find("shapeName", itemIndex)
                if itemFileIndex == -1:
                    itemFileIndex = misString.find("shapename", itemIndex)
                isDts = True
            elif string == "InteriorInstance(":
                itemFileIndex = misString.find("interiorFile", itemIndex)
                if itemFileIndex == -1:
                    itemFileIndex = misString.find("interiorfile", itemIndex)
                isDts = False
            # elif string == "PathedInterior":
            #     itemFileIndex = misString.find("interiorResource", itemIndex)
            #     isDts = False
            else:
                dtsDataBlockIndex = misString.find("dataBlock", itemIndex)
                if dtsDataBlockIndex == -1:
                    dtsDataBlockIndex = misString.find("datablock", itemIndex)
                isDts = True
            itemIndexEnd = misString.find("};", itemIndex)
            # misString[start:end] where start = the next quotation mark after the position index + 1 (so we don't keep the quote in InteriorPosition), 
            # and end is the next quotation mark after that one.
            itemPosition = misString[get_next_quote(misString, itemPositionIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemPositionIndex) + 1)]
            itemRotation = misString[get_next_quote(misString, itemRotationIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemRotationIndex) + 1)]
            itemScale = misString[get_next_quote(misString, itemScaleIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemScaleIndex) + 1)]
            if (not dtsSkinIndex > itemIndexEnd) and (dtsSkinIndex != -1):
                dtsSkin = misString[get_next_quote(misString, dtsSkinIndex) + 1:get_next_quote(misString, get_next_quote(misString, dtsSkinIndex) + 1)]
            # this one does + 3 instead of + 1 to trim the ~/ from the start of the path
            if string == "TSStatic(" or string == "InteriorInstance(":
                itemFile = misString[get_next_quote(misString, itemFileIndex) + 3:get_next_quote(misString, get_next_quote(misString, itemFileIndex) + 3)]
                itemFilePath = Path(activeMisDataPath + itemFile)
            # PathedInteriors don't have the ~ at the start of the path so add 2 instead of 3
            # elif string == "PathedInterior":
            #     itemFile = misString[get_next_quote(misString, itemFileIndex) + 2:get_next_quote(misString, get_next_quote(misString, itemFileIndex) + 2)]
            #     itemFilePath = Path(activeMisDataPath + itemFile)
            # most DTSes are special and need to have a datablock found instead and resolved to an interior file
            else:
                dtsDataBlock = misString[get_next_quote(misString, dtsDataBlockIndex) + 1:get_next_quote(misString, get_next_quote(misString, dtsDataBlockIndex) + 1)]
                if dtsDataBlock.find("GemItem") != -1:
                    dtsDataBlock,dtsSkin = get_gem_item(dtsDataBlock,rand)
                    isGem = True
                # theres 6 different things the beginning of the block can be called so i have to check for all of them
                scriptStringDtsIndex = scriptString.find("ItemData(" + dtsDataBlock)
                if scriptStringDtsIndex == -1:
                    scriptStringDtsIndex = scriptString.find("StaticShapeData(" + dtsDataBlock)
                    if scriptStringDtsIndex == -1:
                        scriptStringDtsIndex = scriptString.find("StaticShapeData(" + str.capitalize(dtsDataBlock))
                        if scriptStringDtsIndex == -1:
                            scriptStringDtsIndex = misString.find("ItemData()" + dtsDataBlock)
                            if scriptStringDtsIndex == -1:
                                scriptStringDtsIndex = misString.find("StaticShapeData(" + dtsDataBlock)
                                if scriptStringDtsIndex == -1:
                                    scriptStringDtsIndex = misString.find("StaticShapeData(" + str.capitalize(dtsDataBlock))
                scriptStringDtsShapeFileIndex = scriptString.find("shapeFile",scriptStringDtsIndex)
                itemFile = scriptString[get_next_quote(scriptString, scriptStringDtsShapeFileIndex) + 1:get_next_quote(scriptString, get_next_quote(scriptString, scriptStringDtsShapeFileIndex) + 1)]
                # for some reason HelpBubbles (and maybe other dtses idk) have their filepath start with platinum/ instead of ~/ or /. god knows why
                itemFile = itemFile[itemFile.find("data"):] if itemFile.find("data") != 0 else itemFile
                itemFilePath = Path(activeMisDataPath + itemFile)
            if len(str(itemFilePath)) > 200:
                print(itemFilePath)
            fileTemp = Path(itemFilePath)
            itemName = fileTemp.name
            if itemName == " " or itemName == "s":
                print(itemName)
            objList.append(dict(position = itemPosition, rotation = itemRotation, scale = itemScale, file = itemFilePath, skin = dtsSkin, name = itemName, dts = isDts, gem = isGem))
            itemIndex = misString.find(string, itemIndexEnd)
        return objList
    # other initialization
    numPathNodesRemoved = 0
    fakeColmesh = str(Path(os.path.realpath(__file__)).parent) + r"\cube.dif"
    stringsToSearchFor = []
    stringsToSearchFor.append("Item()") if include_item == True and include_dts == True else None
    stringsToSearchFor.append("TSStatic(") if include_tsstatic == True and include_dts == True else None
    stringsToSearchFor.append("StaticShape(") if include_static_shape == True and include_dts == True else None
    stringsToSearchFor.append("InteriorInstance(") if include_dif == True else None
    listOfActiveLayerCollections = []
    for layerCollection in bpy.context.view_layer.layer_collection.children:
        if layerCollection.exclude == False:
            layerCollection.exclude = True
            listOfActiveLayerCollections.append(layerCollection)
    # move everything in the collection to a temporary collection
    tempCollection = bpy.data.collections.new("temporaryCollection")
    bpy.context.scene.collection.children.link(tempCollection)
    # print(bpy.context.scene.collection.objects)
    baseCollection = bpy.context.scene.collection
    originalCollectionObjects = list(baseCollection.objects)
    originalCollections = None
    for object in baseCollection.objects:
        oldCollections = object.users_collection
        originalCollections = tuple(oldCollections) if originalCollections == None else None
        tempCollection.objects.link(object) if tempCollection.objects.count() > 0 else None
        tempCollection.instance_offset = object.location
        for collectionParent in oldCollections:
            collectionParent.objects.unlink(object)
        for childObject in object.children_recursive:
            oldCollectionsChildObject = childObject.users_collection
            tempCollection.objects.link(childObject)
            tempCollection.instance_offset = childObject.location
            for collection in oldCollectionsChildObject:
                collection.objects.unlink(childObject)
    # open mis and find interiors and stuff
    misPath = filepath
    activeMis = open(misPath)
    activeMisName = os.path.basename(activeMis.name)
    # create a collection to put all the imported stuff into
    finishedCollection = bpy.data.collections.new(activeMisName)
    bpy.context.scene.collection.children.link(finishedCollection)
    misPathString = str(misPath)
    activeMisDataPath = misPathString[0:misPathString.find("data")]
    activeMisScriptsPath = Path(activeMisDataPath + r"server\scripts")
    misString = activeMis.read()
    activeMis.close
    scriptMegaString = " "
    scriptFileList = glob.glob(str(activeMisScriptsPath)+"\**\*.cs", recursive=True)
    for file in scriptFileList:
        csFile = Path(file).open()
        newScript = csFile.read()
        scriptMegaString = scriptMegaString + newScript
        csFile.close()
    itemList = []
    for string in stringsToSearchFor:
        itemList.extend(find_in_file(misString,string,scriptMegaString,activeMisDataPath,random_gems,allowIllegalMbuGems,allowPlatinumGems))    
    print("done finding items")
    # actually place all the items into blender
    prevImportedNum = 0
    for item in itemList:
        # if not a dts then don't use the dts importer
        if include_path_nodes == False and Path(item["file"]).name == "pathnode.dts":
            print("Removed a PathNode. Total items to import is now " + str((len(itemList) - numPathNodesRemoved)))
            numPathNodesRemoved = numPathNodesRemoved + 1
            continue
        if str(item["name"]).find(".dts") == -1:
            try: 
                print("importing",item["name"])
                io_dif.import_dif.load(context = bpy.context, filepath = item["file"])
                print("imported",item["name"],"successfully")
            except:
                print(item["name"])
                print("import_dif failed on item #" + str(itemList.index(item)) + "! Item name:",str(item["name"]))
                failedDif.append(item["name"])
        else:
            try: 
                print("importing",item["name"])
                if item["name"] != "pack1marble.dts":
                    io_scene_dts.import_dts.load(operator, context, filepath = item["file"], reference_keyframe=reference_keyframe,
                    import_sequences=import_sequences,use_armature=use_armature,debug_report=debug_report)
                    print("imported",item["name"],"successfully")
                else:
                    print("pack1marble.dts is known to freeze the importer for some reason. You will need to add it manually. A placeholder has been placed instead.")
                    io_dif.import_dif.load(context = bpy.context, filepath = fakeColmesh)
            except:
                if item["name"] == "colmesh.dts":
                    print("io_scene_dts cannot import colmesh.dts. An equivalent will be created with a Blender cube")
                    io_dif.import_dif.load(context = bpy.context, filepath = fakeColmesh)                 
                else:
                    print("import_dts failed on item #" + str(itemList.index(item)) + "! Item name:",item["name"])
                    failedDts.append(item["name"])
        itemObject = bpy.data.objects.new(item["name"], None)
        # print(difObject.name)
        bpy.context.scene.collection.objects.link(itemObject)
        # print(bpy.context.scene.collection.objects)
        for object in baseCollection.objects:
        #    print(object.name)               
           if (object.name != "tempobject") and object.name.find(".dif") == -1 and object.name.find(".dts") == -1 and object.parent == None:
                print(object.parent)
                object.parent = itemObject
                print(object.parent)
        # correctly format position rotation etc.
        itemPosition = str.split(item["position"])
        itemRotation = str.split(item["rotation"])
        itemScale = str.split(item["scale"])
        # print((difPosition[2]))
        itemObject.location = (float(itemPosition[0]),float(itemPosition[1]),float(itemPosition[2]))
        itemObject.scale = (float(itemScale[0]),float(itemScale[1]),float(itemScale[2]))
        itemObject.rotation_mode = "AXIS_ANGLE"
        # marble blast's stored rotation values are different than blender's. we need to make the rotation angle negative and move it to the front
        itemObject.rotation_axis_angle = (-float(itemRotation[3]) * (float(math.pi)/180),float(itemRotation[0]),float(itemRotation[1]),float(itemRotation[2]))
        # put the item and its children in the finished collection
        oldCollections = itemObject.users_collection
        finishedCollection.objects.link(itemObject)
        finishedCollection.instance_offset = itemObject.location
        for collection in oldCollections:
            collection.objects.unlink(itemObject)
        for child in itemObject.children_recursive:
            # delete item types that were disabled
            if include_static_interiors == False and child.dif_props.interior_type == "static_interior" and itemObject.name.find(".dif") != -1:
                bpy.data.objects.remove(child)
                continue
            if child != None and include_pathed_interiors == False and ((child.dif_props.interior_type == "pathed_interior") or (child.type == "CURVE" and itemObject.name.find(".dif") != -1)):
                bpy.data.objects.remove(child)
                continue
            if child != None and include_game_entities == False and child.dif_props.interior_type == "game_entity":
                bpy.data.objects.remove(child)
                continue
            if child != None and include_path_triggers == False and child.dif_props.interior_type == "path_trigger":
                bpy.data.objects.remove(child)
                continue
            if child != None and deleteDtsCol == True and itemObject.name.find(".dts") != -1 and str.casefold(child.name).find(str.casefold("Col")) != -1:
                bpy.data.objects.remove(child)
                continue
            if child != None and onlyHighestLod == True and itemObject.name.find(".dts") != -1 and str.casefold(child.name).find(str.casefold("detail")) != -1:
                bpy.data.objects.remove(child)
            else:
                if item["dts"] == True and len(child.material_slots) != 0:
                    print(len(child.material_slots))
                    texNode = None
                    bsdfNode = None
                    renameMaterial = None
                    matOldName = None
                    materialCheckList = []
                    onlyTransparency = False
                    for mat in child.material_slots:
                            if str(mat.material.name).find("base.") != -1:
                                renameMaterial = child.material_slots[list(child.material_slots).index(mat)].material
                                matOldName = renameMaterial.name
                            materialCheckList.append(mat.material)
                    if renameMaterial != None:
                        for textureNode in bpy.data.materials[renameMaterial.name].node_tree.nodes:
                            if textureNode.bl_idname == "ShaderNodeTexImage" and item["skin"] != None:
                                texNode = textureNode
                                imagePath = str(textureNode.image.filepath)
                                newImagePath = imagePath.replace("base",str(item["skin"])) if str(item["skin"]) != "pink" else imagePath
                                try: textureNode.image = bpy.data.images.load(newImagePath)
                                except:
                                    print(newImagePath,"doesn't exist. This was probably a secondary skin such as the grass present around some PQ signs")
                            if textureNode.bl_idname == "ShaderNodeBsdfPrincipled":
                                bsdfNode = textureNode
                        material_check(texNode,renameMaterial,matOldName,item,bsdfNode,attempt_to_fix_transparency)
                        # sometimes DTS files don't have a ShaderNodeTexImage by default so we have to fix that
                    for mat in materialCheckList:
                        nodes = bpy.data.materials[mat.name].node_tree.nodes
                        for node in nodes:
                            onlyTransparency = True if node.bl_idname == "ShaderNodeTexImage" else onlyTransparency
                            texNode = node if node.bl_idname == "ShaderNodeTexImage" else texNode
                            bsdfNode = node if node.bl_idname == "ShaderNodeBsdfPrincipled" else bsdfNode
                        if texNode == None:
                            print(texNode)
                        material_check(texNode,mat,matOldName=(mat.name),item=item,bsdfNode=bsdfNode,attempt_to_fix_transparency=attempt_to_fix_transparency,onlyTransparency=onlyTransparency)
                    if child.type == "MESH":
                        for polygon in child.data.polygons: polygon.use_smooth = True
                oldCollectionsChild = child.users_collection
                finishedCollection.objects.link(child)
                finishedCollection.instance_offset = child.location
                for collection in oldCollectionsChild:
                    collection.objects.unlink(child)
        print((prevImportedNum + 1), "/", len(itemList) - numPathNodesRemoved,"items imported")
        # i tried to use itemList.index(item) but if two items were exactly the same (yes this happens. in vanilla PQ.) it would print the wrong number
        prevImportedNum = prevImportedNum + 1
    # move original objects back to their original collection
    for object in tempCollection.objects:
        for collection in originalCollections:
            collection.objects.link(object)
            collection.instance_offset = object.location
        tempCollection.objects.unlink(object)
        for childObject in object.children_recursive:
            for collection in originalCollections:
                collection.objects.link(childObject)
                collection.instance_offset = childObject.location
            tempCollection.objects.unlink(childObject)
    bpy.data.collections.remove(tempCollection)
    for layerCollection in listOfActiveLayerCollections:
        layerCollection.exclude = False
    return ({"FINISHED"},failedDif,failedDts)

class ImportMis:
    mis = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\lbmissions_pq\test\*.mis"
    mcs = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\lbmissions_pq\test\*.mcs"
    filesList = glob.glob(mis, recursive=False)
    filesListTwo = glob.glob(mcs, recursive=False)
    errorDif = []
    errorDts = []
    failedDif = []
    failedDts = []
    bub = {}
    print("started import")
    for filepath in filesList:      
        print("loading",filepath)
        bub, failedDif, failedDts = load(operator=bpy.types.Operator, context=bpy.context, filepath=filepath)
        errorDts.extend(failedDif)
        errorDif.extend(failedDts)
        for child in bpy.context.scene.collection.children_recursive:
            print("removing object",str(bpy.context.scene.collection.children_recursive.index(child) + 1),"of",str(len(bpy.context.scene.collection.children_recursive)))
            try: bpy.data.objects.remove(child)
            except: 
                for object in child.objects:
                    bpy.data.objects.remove(object)
                bpy.data.collections.remove(object)

    for filepath in filesListTwo:
        print("loading",filepath)
        bub, failedDif, failedDts = load(operator=bpy.types.Operator, context=bpy.context, filepath=filepath)
        errorDts.extend(failedDif)
        errorDif.extend(failedDts)
        for child in bpy.context.scene.collection.children_recursive:
            print("removing objects...")
            try: bpy.data.objects.remove(child)
            except: 
                for object in child.objects:
                    bpy.data.objects.remove(object)
                bpy.data.collections.remove(child)

    print(len(errorDif),"dif and",len(errorDts),"dts failed to import properly!")
    print("Failed imports:",errorDif,errorDts)
        




