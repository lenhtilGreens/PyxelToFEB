# This script converts a PyxelEdit JSON tilemap file into an FEBuilder MAPCHIP_CONFIG file
# to use, enter "python <pyxelJSON.JSON>" from the commandline where <pyxelJSON.JSON> is your file
# or drag and drop your tilemap JSON onto the python script from Windows explorer.

# The script can also incorporate terrain and palette data from a TMX file, as long as
# the TMX file has tilesets named 'paletteData' and 'terrainData' and the TMX shares the same filename
# as the JSON file.

# Output will be the same name as the JSON file but with a MAPCHIP_CONFIG extension. If that file already
# exists, it'll be overwritten.

#Refer to the example files if needed.

import json
import argparse

import xml.etree.ElementTree as ET

#should I just expect a filename instead and share the name across types
# (input JSON, look for corresponding TMX and use if available, output MAPCHIP_CONFIG)
parser = argparse.ArgumentParser(description='Convert a JSON file to MapConfig')
parser.add_argument('JSON', metavar='f', type=str, nargs='+', help='JSON file')

args = parser.parse_args()
v = vars(args)
with open(v['JSON'][0]) as f:
 data = json.load(f)

filename = v['JSON'][0][0:-(len('.json'))]

#check if corresponding TMX file exists
try:
	xmlTree = ET.parse((filename+".tmx"))
except FileNotFoundError:
	print("Terrain and palette will be defaulted to 0x00")
	palDefined = False
	terrainDefined = False
else:
	xmlRoot = xmlTree.getroot()
	
	#skip over "image" and "terraintypes" items (there is probably a better way to access the proper node)
	tmxOffset = 2 
	
	for child in xmlRoot:
		if(child.tag=='tileset'):
			if(child.attrib['name']=='terrainData'):
				print("Terrain found")
				terrainTree = child
				terrainDefined = True
			if(child.attrib['name']=='paletteData'):
				print("Palette found")
				palTree = child
				palDefined = True
#end catch block

#work on the JSON data
tWide = data["tileswide"] #should be 64
tHigh = data["tileshigh"] #should be 64
tWidth = data["tilewidth"] #should be 8
tHeight = data["tileheight"] #should be 8

allLayers = data["layers"] #each Layer is a dict with "number", "tiles", "name"
#Assume all the tiles are stored on a single base layer
mTiles = allLayers[0]["tiles"] #list type (should be 4096 (64^2) long)

#each tile is a dict with the following keys
# x: the x position of the chip on the tileset | FEBuilder will want this in a specific order
# y: the y position of the chip on the tileset | so it doesn't need these values from PyxelEdit JSON
# index: linear index of the tile in the tileset. Arranged in ascending order, so not used in this implementation
# tile: linear chipset index that references what chip is used for this specific tileSet index| FEBuilder will want this info
# flipX: true if the tile is horizontally mirrored for the tileset, false if no change
# rot: if tile is rotated on the tileset (0:none, 1:90, 2:180, 3:270)

#start a new mapconfig file
mapConfigFile = open((filename+".MAPCHIP_CONFIG"),"wb+")
terrainBytes = bytearray()

def getOCode(isFlipX, rotValue):
	if (rotValue=='1' or rotValue=='3'): #90 or 270 degrees
		#doesn't matter if flipped or not, this type of rotation can't be parsed through config
		print("WARNING: rotated tile detected")
		return 0x0000
	if (isFlipX==False and rotValue==0): #0 unflipped
		return 0x0000
	if (isFlipX==True and rotValue==0): #0 flipped
		return 0x0400
	if (isFlipX==False and rotValue==2): #180 unflipped
		return 0x0C00
	if (isFlipX==True and rotValue==2): #180 flipped
		return 0x0800
	print("Unhandled case passed to tile orientation fetcher")
	return 0x0000 ##it's a zero or unhandled case
#end getOCode

def getPalCode(tileIndex, quadrant):
	#quadrant:
	# 0 1
	# 2 3
	#tileIndex is relative to the TMX (1024) tileset
	#so make sure any index passed in from the JSON (4096) tileset is converted prior to passing
	
	palList = palTree[tileIndex+tmxOffset].attrib['terrain'].split(',')
	iCode=palList[quadrant]
	if iCode=='0':
		return 0x0000
	if iCode=='1':
		return 0x1000
	if iCode=='2':
		return 0x2000
	if iCode=='3':
		return 0x3000
	if iCode=='4':
		return 0x4000
	#shouldn't happen/unsupported code
	print("Unsupported code")
	return 0x0000 #anyways
#end getPalCode

scanY=0
#FOR each other row (from 0 -> tHigh-1)
while scanY < (tHigh-1):
	#FOR every other tile (from 0 -> tWide-1)
	scanX = 0
	while scanX < (tWide-1):
		#build a quadrant of the subtiles ((x,y) (x+1,y),(x,y+1),(x+1,y+1))
		originIndex = scanX+(scanY*64) #get the (x,y) origin reference
		lUpper_tile = mTiles[originIndex] # tWide/2 - 1 = 31
		rUpper_tile = mTiles[originIndex + 1] #just the next one over
		lLower_tile = mTiles[originIndex + 64] # tWide/2 = 32
		rLower_tile = mTiles[originIndex + 64 + 1]
		
		#determine palette codes for each tile and quadrant (default zero if no file)
		if (palDefined):
			tmxIndex = scanX//2+32*(scanY//2)
			lUpper_palCode = getPalCode(tmxIndex,0)
			rUpper_palCode = getPalCode(tmxIndex,1)
			lLower_palCode = getPalCode(tmxIndex,2)
			rLower_palCode = getPalCode(tmxIndex,3)
		else:
			lUpper_palCode = 0x0000
			rUpper_palCode = 0x0000
			lLower_palCode = 0x0000
			rLower_palCode = 0x0000
		
		#determine the orientation code for each tile
		lUpper_OCode = getOCode(lUpper_tile["flipX"],lUpper_tile["rot"])
		rUpper_OCode = getOCode(rUpper_tile["flipX"],rUpper_tile["rot"])
		lLower_OCode = getOCode(lLower_tile["flipX"],lLower_tile["rot"])
		rLower_OCode = getOCode(rLower_tile["flipX"],rLower_tile["rot"])
		
		#commit the tile metadata to file
		#LU
		tileCode= lUpper_palCode+lUpper_OCode+lUpper_tile["tile"]
		s = "%04X"%tileCode
		mapConfigFile.write(bytes.fromhex(s[2:4])) #reverse the bytes on each tile
		mapConfigFile.write(bytes.fromhex(s[0:2])) #(e.g. 10 53 -> 53 10)
		#RU
		tileCode= rUpper_palCode+rUpper_OCode+rUpper_tile["tile"]
		s = "%04X"%tileCode
		mapConfigFile.write(bytes.fromhex(s[2:4])) #reverse the bytes on each tile
		mapConfigFile.write(bytes.fromhex(s[0:2])) #(e.g. 10 53 -> 53 10)
		#LL
		tileCode= lLower_palCode+lLower_OCode+lLower_tile["tile"]
		s = "%04X"%tileCode
		mapConfigFile.write(bytes.fromhex(s[2:4])) #reverse the bytes on each tile
		mapConfigFile.write(bytes.fromhex(s[0:2])) #(e.g. 10 53 -> 53 10)
		#RL
		tileCode= rLower_palCode+rLower_OCode+rLower_tile["tile"]
		s = "%04X"%tileCode
		mapConfigFile.write(bytes.fromhex(s[2:4])) #reverse the bytes on each tile
		mapConfigFile.write(bytes.fromhex(s[0:2])) #(e.g. 10 53 -> 53 10)
		
		scanX += 2 #go to the next 'tile'
	scanY += 2 #go to the next 'row'
#endWhile

#mapChipConfig should be  2000bytes at this point if all tiles are actually accomodated for / import files were proper dimensions

#_write terrain data to file_
if terrainDefined==True:
	terrainTileCount = int(terrainTree.attrib["tilecount"]) #should always be 1024
	tileIter=0
	
	while tileIter<terrainTileCount:
		#there are four corners to choose from for terrain, just go with upperLeft(0)
		terrainTile = (terrainTree[tileIter+tmxOffset].attrib['terrain']).split(',')
		mapConfigFile.write(bytes.fromhex("%02x"%(int(terrainTile[0]))))
		tileIter+=1
		# if a tile doesn't have assigned terrains it isn't given an entry in the TMX
		# I will assume the map is complete / each tile assigned terrains
		# since below is missing catches for looking out-of-bounds
		# terrainTileID = int(terrainTree[tileIter+tmxOffset].attrib['id'])
		# if (tileIter != terrainTileID):
			# buffer=tileIter
			# while buffer<terrainTileID)
				# mapConfigFile.write(bytes.fromhex("00"))
				# buffer+=1
else:
	#fill terrain section with empty data (0x00)
	mapConfigFile.write(bytearray(1024))
	
mapConfigFile.close()
print("Done...")
#input("Press Enter to exit...")

