How to convert a tileset to FEBuilder mapconfig and chipset (with PyxelEdit):
1. Get:
	Python3
	PyxelEdit (free is fine)
	GraphicsGale
	FEBuilder
	An insertable tileset (512x512px constructed of 16x16px tiles, under 5x16 colors, etc.)
2. If your tileset is over 16 colors, preserve the palette (details in Notes)
3. Open PyxelEdit
4. Import the tileset
		File->Import Image(s)
		Tile Width: 8
		Tile Height: 8
		Check "Identify Tiles" and "Transformations"
		Click Import
5. Set the chipset width (necessary for proper export)
		Tiles->Change Tileset Width -> enter "32" (afaik "Preserve Tile layout doesn't alter anything but I left it unchecked).
6. Export the chipset. 
		File->"Export Tileset"*
		The resulting chipset should be 256px wide. Depending on the circumstances FEBuilder may need it 256px high as well.
	(*Confusing nomenclature yes, this is a tileset of a tileset. For convenience I call the smaller of the two a chipset.)
7. Export the "tilemap" as JSON (or XML)
	(Free version is just File->"Export Tilemap as XML")
		File ->"Export Tilemap"
		File name : if using a TMX file, have the filename be the same (but different extension)
		File format : XML or JSON
		Click Save
8. Drag and drop the JSON (or XML) file onto the appropriate python script
9. Voila! You have a MAPCONFIG file as well as a chipset to import into FEBuilder. You may need to reload the image palette to recalibrate the color indexes of the chipset.


Notes:
- Free version of PyxelEdit is fine. Use the XML edition of the script.

- Paid version has a fancy coat of paint, JSON export support, and animation support (and ?), but I didn't notice enough of a difference between the two for the purpose of generating chipset data for FEBuilder.
	INSIDE the PyxelEdit tilemap exports though, XML's "index" attribute becomes the "tile" attribute in the JSON (and its version of "index" doesn't exist in the XML)! Be aware of it if working on internals.

- You can preserve your palette by 
	1. Creating a (0,0,0 -> 255,255,255) gradation as a full, unique palette
	2. Affixing the gradation to your index-mode tileset in GraphicsGale (don't match to colors) 
	3. Running PyxelEdit with the image from step 2 and getting your chipset (which will wreck your palette/index order but not your color values)
	4. Loading the gradation palette onto your chipset, this time matching to colors
	5. Loading your original palette, this time not matching to colors (so indexes will be preserved)
	*. The resulting chipset isn't quite ready for FEBuilder import yet, you will need to:
		i. Load the first palette row onto each of the other palette banks
		ii. Merge duplicate colors (now you have a 16 color image FEBuilder will be happy with)
		iii. Reload the original palette (again) so FEBuilder can pull and load it automatically
	** This process won't create palette efficiency but that feels very niche and can also be worked around to some extent by remembering/setting the difference in the TMX file while having duplicate tiles in the PyxelEdit tileset

- I could not get PyxelEdit to create a worthwhile chipset without toggling both Rotation and Mirror efficiencies. Luckily, during the vanilla test only the first chip had unconvertable rotation (90 or 270 degrees), but it's still something to note and watch out for. They are easy enough to manually fix from PyxelEdit (Ctrl+leftClick with the TilePlacer tool to map a rotated chip as a new chip in the chipset with no transformation applied) and to search for within the JSON/XML data (rot="3" or rot="1"). 

If an unconvertable rotation is found, the script will just ignore orientation and use the chip referenced with no transformations applied.

-I assume if a TMX file is being populated with terrain and palette data it'll be complete data (again, easy enough to skim through the TMX file in text to find any missing entries). Script probably produces garbage or breaks on null entries.

-To get the terrain (and palette) entries populated, you can use the tmx file provided as a template or dump the xml data from the list yourself. Tiled will recognize it when you reload the tmx file. I followed FEBuilder's notation for consistency, although in the hexeditor the terrain is one less than what's noted ("Plains" would be 00 in MAPCHIPCONFIG, but 01 in FEBuilder/terrain).

- I presume ascending order's maintained in TMX files, so don't go adding entries and values in willy-nilly and expect it to continue working. Look inside the TMX files if things seem to go awry there.

- If you make a multiPalette chipset yourself and lose track of which palette went where, you can mask the other palette to get a rough idea of which tiles you need to cover on the TMX file for that bank

Even More Notes/Credits:
- Thank you Pik for helping me understand the FEBuilder mapchipconfig data! (And thanks to 7743 for creating FEBuilder)
- Image credit to Dirge for the Famicom Wars tiles and to Jackster for the Fire Emblem NES tile rips used in the example (both via Spriter's Resource)