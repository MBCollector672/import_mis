import bpy
import os
import math
import glob
import random
import bmesh
from pathlib import Path
# import io_dif
from .io_scene_dts import import_dts
from .io_dif import import_dif

def load(operator, context, filepath,
     # mis import configs
    include_dif = True,
    include_dts = True,
    include_static_interiors = True,
    include_pathed_interiors = True,
    include_path_triggers = False,
    include_game_entities = False,
    get_pathed_interiors_from_mis = True,
    get_pathed_interior_by_name = True,
    include_item = True,
    include_static_shape = True,
    include_tsstatic = True,
    include_path_nodes = False,
    attempt_to_fix_transparency = True,
    random_gems = True,
    allow_illegal_mbu_gems = False,
    allow_platinum_gems = False,
    delete_dts_col = True,
    try_only_highest_lod = True,
    recalculate_dts_normals = True,
    use_mbu_pads = True,
    # dts import configs
    reference_keyframe = False,
    import_sequences = False,
    use_armature = False,
    ):
    failedDif = []
    failedDts = []
    gameExtensions = ["mbp","mbg","mbu","pq"]
    def text_node_check(mat):
        nodes = bpy.data.materials[mat.name].node_tree.nodes
        alreadyHasTexNode = False
        for node in nodes:
            if node.bl_idname == "ShaderNodeTexImage":
                alreadyHasTexNode = True
        return alreadyHasTexNode

    def get_item_num(list):
        try: return list["number"]
        except: return list["interiorIndex"]
    def material_check(texNode,mat,matOldName,item,bsdfNode,attempt_to_fix_transparency,onlyTransparency = False,datablock = None, checkTexNode = False):
        fileExtensions = ["",".png",".jpg",".PNG",".JPG","_01.png", "_01.jpg", "_01.JPG", "_01.PNG"]
        if texNode == None and onlyTransparency == False:
        # sometimes the texture node fails to be recognized? either that or somewhere in the code sets it to none. it also fails to remove the texture node even though it
        # recognizes that it exists after trying and failing to remove it. i don't understand why or how but it happens and this fixes it
            alreadyHasTexNode = text_node_check(mat) if onlyTransparency == False and checkTexNode == True else None
            if alreadyHasTexNode == False:
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
                        try: texNode.image = bpy.data.images.load(imagePath)
                        except: 
                            if datablock == "StartPad" or datablock == "EndPad" or datablock == "StartPad_MBG" or datablock == "EndPad_MBG":
                                if matOldName == "whitegreen" or matOldName == "whiteblue":
                                    imagePath = (str(Path(item["file"]).parent)) + "\\white.jpg"
                                    print(texNode.image)
                                    texNode.image = bpy.data.images.load(imagePath)
                                if matOldName == "greenwhite":
                                    imagePath = (str(Path(item["file"]).parent)) + "\\green.jpg"
                                    texNode.image = bpy.data.images.load(imagePath)
                                if matOldName == "bluewhite":
                                    imagePath = (str(Path(item["file"]).parent)) + "\\blue.jpg"
                                    texNode.image = bpy.data.images.load(imagePath)
                            print("No skin found at",imagePath) if texNode.image == None else None
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
                                try: nodes.remove(texNode)
                                except: print("Failed to remove",texNode)
                                texNode = ""
                                if item["name"].find("(import_mis placeholder)") != -1:
                                    bsdfNode.inputs["Base Color"].default_value = (231,0,225,255)
                    if texNode != "":
                        bpy.data.materials[mat.name].node_tree.links.new(texNode.outputs["Color"], bsdfNode.inputs["Base Color"])
                        print("used image is" + str(texNode.image))
        # couple of fixes for weird transparency shenanigans
        if texNode != "" and texNode != None and item["gem"] == True and texNode.image.name.find("gemshine") == -1:
            bpy.data.images[texNode.image.name].alpha_mode = 'NONE'
        if texNode != "" and texNode != None and (texNode.image != None and texNode.image.name.find("finishback_01") != -1 or texNode.image != None and texNode.image.name.find("finishsign_01") != -1):
            bpy.data.images[texNode.image.name].alpha_mode = 'NONE'
        # turning on transparency if the prop is supposed to be transparent
        if texNode != "" and texNode != None and mat.torque_props.use_transparency == True and attempt_to_fix_transparency == True:
            bpy.data.materials[mat.name].node_tree.links.new(texNode.outputs["Alpha"], bsdfNode.inputs["Alpha"])

    def find_in_file(misString, string, scriptString, activeMisDataPath, rand, allow_illegal_mbu_gems, allow_platinum_gems):

        mbgValidGems = ["red", "yellow", "blue", "base", "purple", "green", "turquoise", "orange", "black"]
        mbuValidGems = ["red", "yellow", "blue"]
        mbuIllegalGems = ["base", "purple", "green", "turquoise", "orange", "black", "white"]
        pqValidGems = ["red", "yellow", "blue", "base", "purple", "green", "turquoise", "orange", "black", "platinum"]
        def get_next_quote(misString, index):
            return misString.find("\"", index)
        
        def get_gem_item(dataBlock, rand):
            # change gem lists depending on settings
            mbuValidGems.extend(mbuIllegalGems) if allow_illegal_mbu_gems == True else None
            mbuValidGems.append("platinum") if allow_platinum_gems == True else None
            mbgValidGems.append("platinum") if allow_platinum_gems == True else None
            newDataBlock = None
            game = None
            # find the gem's type (game) and color (skin)
            if str.casefold(dataBlock).find("candy") != -1:
                color = str.casefold(dataBlock[9:])
                if color == "red":
                    color = "base"
                elif color == "yellow":
                    color = "orange"
                elif color == "blue":
                    color = "black"
                # yes candy is technically a gem but the transparency on candy is actually needed and isGem tells the program to turn the transparency off if it's true
                return (dataBlock,color,False)
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
            return(newDataBlock,color,True)


        
        itemIndex = misString.find(string)
        objList = []
        # run misString.find last so its value is checked before the while loop runs again
        while(itemIndex != -1):
            # indexes of all the values we need to store and use in blender
            isGem = False
            dtsSkin = None
            dtsDataBlock = None
            itemSmoothingType = None
            itemInteriorIndex = None
            # this is a pretty trash fix for some SimGroups not being PathedInteriors. i added this pretty late and i am too lazy to make it properly
            dontAppend = False
            itemPositionIndex = misString.find("position", itemIndex)
            itemRotationIndex = misString.find("rotation", itemIndex)
            itemScaleIndex = misString.find("scale", itemIndex)
            dtsSkinIndex = misString.find("skin", itemIndex)
            if string == "TSStatic(":
                itemFileIndex = str.casefold(misString).find("shapename", itemIndex)
                isDts = True
            elif string == "InteriorInstance(":
                itemFileIndex = str.casefold(misString).find("interiorfile", itemIndex)
                isDts = False
            elif string == "SimGroup(":
                nextSimGroupIndex = misString.find(string,itemIndex + 1)
                pathedInteriorIndex = str.casefold(misString).find("pathedinterior(",itemIndex)
                # if the simgroup doesn't have a pathed interior then skip it
                if (pathedInteriorIndex < nextSimGroupIndex and pathedInteriorIndex > 0 ) or (pathedInteriorIndex > 0 and nextSimGroupIndex < 0):
                    itemPositionIndex = str.casefold(misString).find("position", pathedInteriorIndex)
                    itemRotationIndex = str.casefold(misString).find("rotation", pathedInteriorIndex)
                    itemScaleIndex = str.casefold(misString).find("scale", pathedInteriorIndex)
                    interiorResourceIndex = str.casefold(misString).find("interiorresource",pathedInteriorIndex)
                    interiorIndexIndex = str.casefold(misString).find("interiorindex",pathedInteriorIndex)
                    itemFile = misString[get_next_quote(misString, interiorResourceIndex) + 1:get_next_quote(misString, get_next_quote(misString,interiorResourceIndex) + 1)]
                    itemFile = itemFile[itemFile.find("data"):] if itemFile.find("data") != 0 else itemFile
                    itemFilePath = Path(activeMisDataPath + itemFile)
                    itemInteriorIndex = int(misString[get_next_quote(misString, interiorIndexIndex) + 1:get_next_quote(misString, get_next_quote(misString,interiorIndexIndex) + 1)])
                    # find the marker with seqnum 0 and use its smoothing type for the object's smoothing type (sometimes difs don't have smoothing types defined)
                    itemPathIndex = str.casefold(misString).find("new path(", itemIndex)
                    itemMarkerIndex = str.casefold(misString).find("marker(", itemPathIndex)
                    itemSeqNumIndex = str.casefold(misString).find("seqnum", itemMarkerIndex)
                    itemSeqNum = misString[get_next_quote(misString, itemSeqNumIndex) + 1:get_next_quote(misString, get_next_quote(misString,itemSeqNumIndex) + 1)]
                    # sometimes paths don't start at seqNum 0, so get the settings of the lowest seqNum
                    if itemSeqNum != 0:
                        lowestNumberIndex = itemSeqNumIndex
                        lowestSeqNum = itemSeqNum
                        lowestSeqNumMarkerIndex = itemMarkerIndex
                        itemMarkerIndex = str.casefold(misString).find("marker(", itemMarkerIndex + 1)
                        itemSeqNumIndex = str.casefold(misString).find("seqnum", itemMarkerIndex)
                        while itemSeqNumIndex < nextSimGroupIndex and itemSeqNumIndex != -1:
                            itemSeqNum = misString[get_next_quote(misString, itemSeqNumIndex) + 1:get_next_quote(misString, get_next_quote(misString,itemSeqNumIndex) + 1)]
                            if itemSeqNum < lowestSeqNum:
                                lowestNumberIndex = itemSeqNumIndex
                                lowestSeqNum = itemSeqNum
                                lowestSeqNumMarkerIndex = itemMarkerIndex
                            itemMarkerIndex = str.casefold(misString).find("marker(", itemMarkerIndex + 1)
                            itemSeqNumIndex = str.casefold(misString).find("seqnum", itemMarkerIndex)
                        itemMarkerIndex = lowestSeqNumMarkerIndex
                    itemSmoothingTypeIndex = str.casefold(misString).find("smoothingtype",itemMarkerIndex)
                    itemSmoothingType = misString[get_next_quote(misString, itemSmoothingTypeIndex) + 1:get_next_quote(misString, get_next_quote(misString,itemSmoothingTypeIndex) + 1)]
                    isDts = False
                else:
                    dontAppend = True
            else:
                dtsDataBlockIndex = str.casefold(misString).find("datablock", itemIndex)
                isDts = True
            if dontAppend == False:
                itemIndexEnd = misString.find("};", itemIndex)
                # misString[start:end] where start = the next quotation mark after the position index + 1 (so we don't keep the quote in InteriorPosition), 
                # and end is the next quotation mark after that one.
                itemPosition = misString[get_next_quote(misString, itemPositionIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemPositionIndex) + 1)]
                itemRotation = misString[get_next_quote(misString, itemRotationIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemRotationIndex) + 1)]
                itemScale = misString[get_next_quote(misString, itemScaleIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemScaleIndex) + 1)]
                if (not dtsSkinIndex > itemIndexEnd) and (dtsSkinIndex != -1):
                    dtsSkin = misString[get_next_quote(misString, dtsSkinIndex) + 1:get_next_quote(misString, get_next_quote(misString, dtsSkinIndex) + 1)]
                if string == "TSStatic(" or string == "InteriorInstance(":
                    itemFile = misString[get_next_quote(misString, itemFileIndex) + 1:get_next_quote(misString, get_next_quote(misString, itemFileIndex) + 1)]
                    itemFile = itemFile[itemFile.find("data"):] if itemFile.find("data") != 0 else itemFile
                    itemFilePath = Path(activeMisDataPath + itemFile)
                # most DTSes are special and need to have a datablock found instead and resolved to an interior file
                elif string == "SimGroup(":
                    pass
                else:
                    dtsDataBlock = misString[get_next_quote(misString, dtsDataBlockIndex) + 1:get_next_quote(misString, get_next_quote(misString, dtsDataBlockIndex) + 1)]
                    if str.casefold(dtsDataBlock).find("gemitem") != -1 or str.casefold(dtsDataBlock).find("candyitem") != -1:     
                        dtsDataBlock,dtsSkin,isGem = get_gem_item(dtsDataBlock,rand)
                    # this game adores messing with capitalization for some reason so we gotta casefold everything
                    scriptStringDtsIndex = str.casefold(scriptString).find("itemdata(" + str.casefold(dtsDataBlock))
                    if scriptStringDtsIndex == -1:
                        scriptStringDtsIndex = str.casefold(scriptString).find("staticshapedata(" + str.casefold(dtsDataBlock))
                        if scriptStringDtsIndex == -1:
                            scriptStringDtsIndex = str.casefold(misString).find("staticshapedata(" + str.casefold(dtsDataBlock))
                            if scriptStringDtsIndex == -1:
                                scriptStringDtsIndex = str.casefold(misString).find("itemdata(" + str.casefold(dtsDataBlock))
                    # hardcoded fix for a few mbxp shapes being before the default shapes in the script string for some reason
                    if dtsDataBlock == "StartPad" or dtsDataBlock == "EndPad":
                        scriptStringDtsIndex = str.casefold(scriptString).find("staticshapedata(" + str.casefold(dtsDataBlock) + ")")
                    # hardcoded fix for mbg and mbp pads not loading their textures
                    if dtsDataBlock == "StartPad" or dtsDataBlock == "EndPad" or dtsDataBlock == "StartPad_MBG" or dtsDataBlock == "EndPad_MBG":
                        dtsSkin = "fix the pad skin"
                    scriptStringDtsShapeFileIndex = str.casefold(scriptString).find("shapefile",scriptStringDtsIndex)
                    itemFile = scriptString[get_next_quote(scriptString, scriptStringDtsShapeFileIndex) + 1:get_next_quote(scriptString, get_next_quote(scriptString, scriptStringDtsShapeFileIndex) + 1)]
                    # for some reason HelpBubbles (and maybe other dtses idk) have their filepath start with platinum/ instead of ~/ or /. god knows why
                    itemFile = itemFile[itemFile.find("data"):] if itemFile.find("data") != 0 else itemFile
                    itemFilePath = Path(activeMisDataPath + itemFile)
                fileTemp = Path(itemFilePath)
                itemName = fileTemp.name
                # fix mbu pads defaulting to mbm pads for some reason
                if dtsDataBlock == "StartPad_MBM" or dtsDataBlock == "EndPad_MBM" and use_mbu_pads == True:
                    itemFilePath = Path(str(itemFilePath).replace(itemName,"mbu\\"+ itemName))
                # fixing checkpoint is a bit more involved
                elif dtsDataBlock != None and str.casefold(dtsDataBlock) == "checkpoint" and isMBU == True and use_mbu_pads == True:
                    checkPadPath = glob.glob(activeMisDataPath + "\\**\\pads\\checkpad.dts", recursive=True)
                    itemFilePath = Path(checkPadPath[0])
                    itemName == "checkpad.dts"
                    tempScaleList = str.split(itemScale)
                    for num in tempScaleList: tempScaleList[tempScaleList.index(num)] = float(num) * 2
                    itemScale = (str(tempScaleList[0]) + " " + str(tempScaleList[1]) + " " + str(tempScaleList[2]))
                if itemName == " ":
                    print(itemName)
                objList.append(dict(position = itemPosition, rotation = itemRotation, scale = itemScale, file = itemFilePath, 
                                    skin = dtsSkin, name = itemName, dts = isDts, gem = isGem, dataBlock = dtsDataBlock, smoothingType = itemSmoothingType, interiorIndex = itemInteriorIndex))
            if string != ("SimGroup("): 
                itemIndex = misString.find(string, itemIndexEnd)
            else:
                # using the next SimGroup instead of the end of the item index because that doesn't work for SimGroups. adding 1 so it doesn't find the previous SimGroup
                itemIndex = misString.find(string, itemIndex + 1)
        return objList
    # other initialization
    numPathNodesRemoved = 0
    fakeColmesh = str(Path(os.path.realpath(__file__)).parent) + r"\cube.dif"
    octahedronDif = str(Path(os.path.realpath(__file__)).parent) + r"\octahedron.dif"
    coloredTileMazeLookupTable = str(Path(os.path.realpath(__file__)).parent) + r"\coloredtilemazelookuptable.txt"
    stringsToSearchFor = []
    stringsToSearchFor.append("Item()") if include_item == True and include_dts == True else None
    stringsToSearchFor.append("TSStatic(") if include_tsstatic == True and include_dts == True else None
    stringsToSearchFor.append("StaticShape(") if include_static_shape == True and include_dts == True else None
    stringsToSearchFor.append("InteriorInstance(") if include_dif == True else None
    stringsToSearchFor.append("SimGroup(") if include_pathed_interiors == True and get_pathed_interiors_from_mis == True else None
    listOfActiveLayerCollections = []
    for layerCollection in bpy.context.view_layer.layer_collection.children:
        if layerCollection.exclude == False:
            layerCollection.exclude = True
            listOfActiveLayerCollections.append(layerCollection)
    # move everything in the collection to a temporary collection
    tempCollection = bpy.data.collections.new("temporaryCollection")
    bpy.context.scene.collection.children.link(tempCollection)
    baseCollection = bpy.context.scene.collection
    originalCollectionObjects = list(baseCollection.objects)
    originalCollections = None
    for object in baseCollection.objects:
        oldCollections = object.users_collection
        originalCollections = tuple(oldCollections) if originalCollections == None else None
        tempCollection.objects.link(object) if len(tempCollection.objects) > 0 else None
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
    isMBU = True if misString.find("game = \"Ultra\";") != -1 else False
    activeMis.close
    if activeMisName == "ColoredTileMaze.mcs":
        # i am not paid enough to deal with this
        activeMis = open(coloredTileMazeLookupTable)
        misString = activeMis.read()
        activeMis.close
    scriptMegaString = " "
    # find all the script files and add them to a giant string for datablock locating purposes
    scriptFileList = glob.glob(str(activeMisScriptsPath)+"\**\*.cs", recursive=True)
    for file in scriptFileList:
        csFile = Path(file).open()
        newScript = csFile.read()
        scriptMegaString = scriptMegaString + newScript
        csFile.close()
    itemList = []
    for string in stringsToSearchFor:
        itemList.extend(find_in_file(misString,string,scriptMegaString,activeMisDataPath,random_gems,allow_illegal_mbu_gems,allow_platinum_gems))
    # separate pathed interiors into their own list
    pathedInteriorList = []
    if get_pathed_interiors_from_mis == True and get_pathed_interior_by_name == True:
        for item in itemList:
            if item["interiorIndex"] != None:
                pathedInteriorList.append(item)
    for item in pathedInteriorList:
        itemList.remove(item)    
    print("done finding items")
    # actually place all the items into blender
    prevImportedNum = 0
    for item in itemList:
        # if not a dts then don't use the dts importer
        if include_path_nodes == False and Path(item["file"]).name == "pathnode.dts":
            numPathNodesRemoved = numPathNodesRemoved + 1
            print("Removed a PathNode. Total items to import is now " + str((len(itemList) - numPathNodesRemoved)))
            continue
        if str(item["name"]).find(".dts") == -1:
            try: 
                print("importing",item["name"])
                import_dif.load(context = bpy.context, filepath = item["file"])
                print("imported",item["name"],"successfully")
                # sometimes the mis has the incorrect path and PQ automatically corrects it so we need to account for that
            except FileNotFoundError as exception:
                succeededFix = False
                if str(item["file"]).find("interiors_") == -1:
                    for extension in gameExtensions:
                        newPath = Path(str(item["file"]).replace("interiors","interiors_" + extension))
                        try: 
                            import_dif.load(context = bpy.context, filepath = newPath)
                            succeededFix = True
                            break
                        except FileNotFoundError as exception:
                            continue
                        except:
                            print(item["file"])
                            print("import_dif failed on item #" + str(itemList.index(item)) + "! Item name:",str(item["name"]))
                            failedDif.append(item["name"])
                # ' in interior file paths has a \ added before it. this makes the path invalid so we need to see if this is happening and remove it
                if str(item["file"]).find(r"\'") != -1:
                    newPath = Path(str(item["file"]).replace(r"\'","'"))
                    try: 
                        import_dif.load(context = bpy.context, filepath = newPath)
                        succeededFix = True
                    except FileNotFoundError as exception:
                        continue
                    except:
                        print(item["file"])
                        print("import_dif failed on item #" + str(itemList.index(item)) + "! Item name:",str(item["name"]))
                        failedDif.append(item["name"])
                if succeededFix == False:
                    print(item["file"])
                    print("import_dif failed on item #" + str(itemList.index(item)) + "! Could not find file:",str(item["name"]))
                    failedDif.append(item["name"])
            except:
                print(item["file"])
                print("import_dif failed on item #" + str(itemList.index(item)) + "! Item name:",str(item["name"]))
                failedDif.append(item["name"])
        else:
            try: 
                # a few very specific dts files cause an infinite loop specifically when called from this script. loading through blender works fine. don't try to import
                # if one of those is detected
                print("importing",item["name"])
                if item["name"] != "pack1marble.dts" and item["name"] != "pack2marble.dts":
                    import_dts.load(operator, context, filepath = item["file"], reference_keyframe=reference_keyframe,
                    import_sequences=import_sequences,use_armature=use_armature)
                    print("imported",item["name"],"successfully")
                    if (item["dataBlock"] == "EndPad_MBM" and use_mbu_pads == True) or item["dataBlock"] == "EndPad_MBU":
                        lightBeamPath = str(item["file"]).replace(item["name"],"lightbeam.dts")
                        import_dts.load(operator, context, filepath = lightBeamPath, reference_keyframe=reference_keyframe,
                                                     import_sequences=import_sequences,use_armature=use_armature)
                        print("imported lightbeam.dts successfully")
                else:
                    print(item["name"],"is known to freeze the mis importer for some reason. You will need to add it manually using io_scene_dts. A placeholder has been placed instead.")
                    import_dif.load(context = bpy.context, filepath = fakeColmesh)
                    item["name"] = item["name"][:str(item["name"]).find(".dts")] + " (import_mis placeholder).dts"
                    # colmesh doesn't load so create a cube instead
            except:
                if item["name"] == "colmesh.dts":
                    print("io_scene_dts cannot import colmesh.dts. An equivalent will be created with a Blender cube")
                    import_dif.load(context = bpy.context, filepath = fakeColmesh)
                    item["name"] = "Colmesh (import_mis placeholder).dts"
                elif item["name"] == "octahedron.dts":
                    print("io_scene_dts cannot import octahedron.dts. An equivalent will be created instead")
                    import_dif.load(context = bpy.context, filepath = octahedronDif)                 
                else:
                    print("import_dts failed on item #" + str(itemList.index(item)) + "! Item name:",item["name"])
                    failedDts.append(item["name"])
        itemObject = bpy.data.objects.new(item["name"], None)
        # print(difObject.name)
        bpy.context.scene.collection.objects.link(itemObject)
        # print(bpy.context.scene.collection.objects)
        prevObject = None
        prevItemNum = None
        objectList = []
        curveList = []
        pathedInteriorsWithMatchingNames = list(filter(lambda pathed: pathed["name"] == item["name"], pathedInteriorList)) if item["dts"] == False else None
        for object in baseCollection.objects:
        #    print(object.name)               
           if object.name.find(".dif") == -1 and object.name.find(".dts") == -1 and object.parent == None:
                object.parent = itemObject
                # only do all this stuff if we want to get the pathed interiors from the mis file
                if get_pathed_interiors_from_mis == True and item["dts"] == False and len(pathedInteriorList) > 0:
                    if get_pathed_interior_by_name == False:
                        if item["interiorIndex"] == None:
                            if object.type == "CURVE": bpy.data.objects.remove(object)
                            elif object.dif_props.interior_type == "path_trigger" or object.dif_props.interior_type == "game_entity":
                                pass
                            else:
                                # getting the number associated with the object (object should be named Object.XYZ. we want the XYZ)
                                itemNum = int(object.name[len("Object."):]) if len(object.name) > 6 else 0
                                # we want to keep only the smallest one as that's the base interior
                                if prevItemNum == None:
                                    prevItemNum = itemNum
                                elif itemNum < prevItemNum and prevObject != None:
                                    bpy.data.objects.remove(prevObject)
                                    prevItemNum = itemNum
                                    prevObject = object
                                elif itemNum > prevItemNum:
                                    bpy.data.objects.remove(object)
                    if item["interiorIndex"] != None or get_pathed_interior_by_name == True:
                        # this is the pathed interior so delete anything that isn't a mesh or curve
                        if object.type == "MESH":
                            itemNum = int(object.name[len("Object."):]) if len(object.name) > 6 else 0
                            objectList.append(dict(number = itemNum, object = object))
                        elif object.type == "CURVE":
                            itemNum = int(object.name[len("path."):]) if len(object.name) > 6 else 0
                            curveList.append(dict(number = itemNum, curve = object))
                        else:
                            bpy.data.objects.remove(object) if get_pathed_interior_by_name == False else None

        # remove every object that isn't the interiorIndex + 2-th greatest object number. example: if interiorIndex 0 then we remove all but the 2nd greatest object number
        # as the second imported object will be interiorIndex 0
        if len(objectList) > 0:
            objectList.sort(key=get_item_num)
            curveList.sort(key=get_item_num)
            pathedInteriorsWithMatchingNames.sort(key=get_item_num)
            for object in objectList:
                if get_pathed_interior_by_name == False:
                    if objectList[item["interiorIndex"] + 1]["object"] != object["object"]:
                        bpy.data.objects.remove(object["object"])
                    else:
                        print("Didn't delete",object)
                        object["object"].dif_props.marker_type = str.casefold(item["smoothingType"])
                else:
                    if object == objectList[0]:
                        objPosition = str.split(item["position"])
                        objRotation = str.split(item["rotation"])
                        objScale = str.split(item["scale"])
                    else:
                        objPosition = str.split(pathedInteriorsWithMatchingNames[objectList.index(object) - 1]["position"])
                        objRotation= str.split(pathedInteriorsWithMatchingNames[objectList.index(object) - 1]["rotation"])
                        objScale = str.split(pathedInteriorsWithMatchingNames[objectList.index(object) - 1]["scale"])
                    try:
                        object["object"].location = (float(objPosition[0]),float(objPosition[1]),float(objPosition[2]))
                    except:
                        print("Object position value is invalid!")
                        object["object"].location = (0,0,0)
                    try:
                        object["object"].scale = (float(objScale[0]),float(objScale[1]),float(objScale[2]))
                    except:
                        print("Object scale value is invalid!")
                        object["object"].scale = (0,0,0)
                    object["object"].rotation_mode = "AXIS_ANGLE"
                    # marble blast's stored rotation values are different than blender's. we need to make the rotation angle negative and move it to the front
                    try:
                        object["object"].rotation_axis_angle = (-float(objRotation[3]) * (float(math.pi)/180),float(objRotation[0]),float(objRotation[1]),float(objRotation[2]))
                    except: 
                        print("Object rotation value is invalid!")
                        object["object"].rotation_axis_angle = (0,1,0,0)
                    if objectList.index(object) > 0:
                        object["object"].dif_props.marker_type = str.casefold(pathedInteriorsWithMatchingNames[objectList.index(object) - 1]["smoothingType"])
            # paths are slightly different as the base interior never has a path so omit the + 1
            for curve in curveList: 
                if get_pathed_interior_by_name == False:
                    if curveList[item["interiorIndex"]]["curve"] != curve["curve"]:
                        bpy.data.objects.remove(curve["curve"])
                    else:
                        print("Didn't delete",curve)
                else:
                    pass
        if get_pathed_interiors_from_mis == False or item["dts"] == True or len(pathedInteriorList) == 0:
            # correctly format position rotation etc.
            itemPosition = str.split(item["position"])
            itemRotation = str.split(item["rotation"])
            itemScale = str.split(item["scale"])
            try:
                itemObject.location = (float(itemPosition[0]),float(itemPosition[1]),float(itemPosition[2]))
            except:
                print("Object position value is invalid!")
                itemObject.location = (0,0,0)
            try:
                itemObject.scale = (float(itemScale[0]),float(itemScale[1]),float(itemScale[2]))
            except:
                print("Object scale value is invalid!")
                itemObject.scale = (0,0,0)
            itemObject.rotation_mode = "AXIS_ANGLE"
            # marble blast's stored rotation values are different than blender's. we need to make the rotation angle negative and move it to the front
            try:
                itemObject.rotation_axis_angle = (-float(itemRotation[3]) * (float(math.pi)/180),float(itemRotation[0]),float(itemRotation[1]),float(itemRotation[2]))
            except: 
                print("Object rotation value is invalid!")
                itemObject.rotation_axis_angle = (0,1,0,0)
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
            if child != None and delete_dts_col == True and itemObject.name.find(".dts") != -1 and str.casefold(child.name).find(str.casefold("Col")) != -1:
                bpy.data.objects.remove(child)
                continue
            if child != None and try_only_highest_lod == True and itemObject.name.find(".dts") != -1 and str.casefold(child.name).find(str.casefold("detail")) != -1:
                bpy.data.objects.remove(child)
            else:
                if item["dts"] == True and len(child.material_slots) != 0:
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
                                # sometimes material names have the wrong file extension in them for some reason, if image fails to load then try the other extension
                                except:
                                    if newImagePath.find(".jpg") != -1:
                                        newImagePath = newImagePath.replace(".jpg",".png")
                                        try: textureNode.image = bpy.data.images.load(newImagePath)
                                        except: print(newImagePath,"doesn't exist. This was probably a secondary skin or the color of the base skin")
                                    elif newImagePath.find(".png") != -1:
                                        newImagePath = newImagePath.replace(".png",".jpg")
                                        try: textureNode.image = bpy.data.images.load(newImagePath)
                                        except: print(newImagePath,"doesn't exist. This was probably a secondary skin or the color of the base skin")
                                    else:
                                        extensions = [".png",".jpg"]
                                        for extension in extensions:
                                            newImagePathWithExtension = newImagePath + extension
                                            try: textureNode.image = bpy.data.images.load(newImagePathWithExtension)
                                            except: print(newImagePathWithExtension,"doesn't exist. This was probably a secondary skin or the color of the base skin")
                            if textureNode.bl_idname == "ShaderNodeBsdfPrincipled":
                                bsdfNode = textureNode
                        material_check(texNode,renameMaterial,matOldName,item,bsdfNode,attempt_to_fix_transparency,datablock = item["dataBlock"])
                        # sometimes DTS files don't have a ShaderNodeTexImage by default so we have to fix that
                    for mat in materialCheckList:
                        nodes = bpy.data.materials[mat.name].node_tree.nodes
                        for node in nodes:
                            onlyTransparency = True if node.bl_idname == "ShaderNodeTexImage" else onlyTransparency
                            texNode = node if node.bl_idname == "ShaderNodeTexImage" else texNode
                            bsdfNode = node if node.bl_idname == "ShaderNodeBsdfPrincipled" else bsdfNode
                        if texNode == None:
                            print(texNode)
                        if mat.name == "whitegreen" or mat.name == "greenwhite" or mat.name == "whiteblue" or mat.name == "bluewhite":
                            texNode = None
                            onlyTransparency = False
                        material_check(texNode,mat,matOldName=(mat.name),item=item,bsdfNode=bsdfNode,attempt_to_fix_transparency=attempt_to_fix_transparency,onlyTransparency=onlyTransparency,datablock = item["dataBlock"],checkTexNode = True)
                    if child.type == "MESH":
                        for polygon in child.data.polygons: polygon.use_smooth = True
                        if recalculate_dts_normals == True:
                            bm = bmesh.new()
                            bm.from_mesh(child.data)
                            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
                            bm.to_mesh(child.data)
                            bm.clear()
                            child.data.update()
                            bm.free()
                oldCollectionsChild = child.users_collection
                finishedCollection.objects.link(child)
                finishedCollection.instance_offset = child.location
                for collection in oldCollectionsChild:
                    collection.objects.unlink(child)
        print((prevImportedNum + 1), "/", len(itemList) - numPathNodesRemoved,"items positioned")
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
    return {"FINISHED"}

# class ImportMis:
#     start_time = time.time()
#     mis = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\multiplayer\test\**\*.mis"
#     mcs = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\multiplayer\test\**\*.mcs"
#     # dif = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\**\*.dif"
#     # dts = r"S:\downloads\PlatinumQuest-Dev-master\PlatinumQuest-Dev-master\Marble Blast Platinum\platinum\data\**\*.dts"
#     filesList = glob.glob(mis, recursive=True)
#     filesList.extend(glob.glob(mcs, recursive=True))
#     # difList = glob.glob(dif, recursive=True)
#     # dtsList = glob.glob(dts, recursive=True)
#     errorDif = []
#     errorDts = []
#     failedDif = []
#     failedDts = []
#     bub = {}
#     baseCollection = bpy.context.scene.collection
#     originalCollectionObjects = list(baseCollection.objects)
#     for collection in originalCollectionObjects:
#         bpy.data.collections.remove(collection)
#     print("started import")
#     for filepath in filesList:      
#         print("loading",filepath)
#         bub, failedDif, failedDts = load(operator=bpy.types.Operator, context=bpy.context, filepath=filepath)
#         errorDts.extend(failedDts)
#         errorDif.extend(failedDif)
#         # for child in bpy.context.scene.collection.children_recursive:
#         #     print("removing objects...")
#         #     try: bpy.data.objects.remove(child)
#         #     except: 
#         #         for object in child.objects:
#         #             bpy.data.objects.remove(object)
#         #         bpy.data.collections.remove(child)

#     # originalCollectionObjects = list(baseCollection.objects)
#     # for collection in originalCollectionObjects:
#     #     bpy.data.collections.remove(collection)

#     # for difFile in difList:
#     #     print("loading",difFile)
#     #     try: io_dif.import_dif.load(context=bpy.context, filepath=difFile)
#     #     except EOFError as exception: 
#     #         errorDif.append(difFile)
#     #         print(exception)
#     #     for child in bpy.context.scene.collection.children_recursive:
#     #         print("removing objects...")
#     #         try: bpy.data.objects.remove(child)
#     #         except: 
#     #             for object in child.objects:
#     #                 bpy.data.objects.remove(object)
#     #             bpy.data.collections.remove(child)
#     # print("Failed imports:",errorDif)
#     # for dtsFile in dtsList:
#     #     print("loading",dtsFile, Path(dtsFile).name)
#     #     if Path(dtsFile).name.find("pack") == -1 or Path(dtsFile).name.find("marble") == -1:
#     #         if dtsFile.find("snowball.dts") == -1:
#     #             try: io_scene_dts.import_dts.load(operator=bpy.types.Operator, context=bpy.context, filepath=dtsFile,reference_keyframe=False,
#     #                 import_sequences=False,use_armature=False,debug_report=False)
#     #             except: errorDts.append(dtsFile)
#     #             for child in bpy.context.scene.collection.children_recursive:
#     #                 print("removing objects...")
#     #                 try: bpy.data.objects.remove(child)
#     #                 except: 
#     #                     for object in child.objects:
#     #                         bpy.data.objects.remove(object)
#     #                     bpy.data.collections.remove(child)
#     #     else:
#     #         print("DTS is a packmarble, not importing")

#     end_time = time.time()
#     print(end_time - start_time,"seconds elapsed")
#     print(len(errorDif),"dif and",len(errorDts),"dts failed to import properly!")
#     print("Failed imports:",errorDif,errorDts)
        




