#!/usr/bin/env python
import argparse, re, os, json, sys
import fitsClasses, filedb
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Reads FITS files produced by the Wide Field Camera and attempts an online reduction.')
	parser.add_argument('--datapath', type=str, default = '.', help='Path where the FITS files are. Default: current directory.')
	parser.add_argument('--workingpath', type=str, default = '.', help='Path for the working and reduction files. Default: current directory.')
	parser.add_argument('object', type=str, help='Object name as specified in the FITS header.')
	parser.add_argument('--debug', action='store_true', help='Print some extra debug information.')
	parser.add_argument('-R', '--recursive', action='store_true', help='Look in sub-folders too.')
	args = parser.parse_args()
	print args
	
	objectFilenameDB = "objectdb.json"
	
	objectName = args.object
	datapath = args.datapath
	workingpath = args.workingpath
	debug = args.debug
	
	searchString = ".*.(fits|fits.gz|fits.fz|fit)"
	search_re = re.compile(searchString)
	
	fitsFiles = []
	# Find all folders in data path
	folders = os.walk(datapath)
	subFolders = []
	FITSFilenames = []
	for f in folders:
		resolvedPath = os.path.realpath(f[0])
		if debug: print("Searching for fits files in path: %s"%resolvedPath)
		subFolders.append(os.path.realpath(f[0]))
		for filename in f[2]:
			m = search_re.match(filename)
			if (m): 
				FITSFilenames.append(os.path.join(resolvedPath, filename))
				# print FITSFilenames[-1]
		print "%d FITS files in the directory %s"%(len(FITSFilenames), resolvedPath)
		if not args.recursive: break
	
	FITSFilenames = sorted(FITSFilenames)	
	
	fileDB = filedb.filedb(debug = debug)
	fileDB.load()
	
	newFiles = fileDB.getNewFilenames(FITSFilenames)
			
	print "%d files are new."%len(newFiles)
	 
	objectFITSFiles = []
	for f in newFiles:
		newImage = fitsClasses.fitsObject(debug=debug)
		newImage.initFromFITSFile(f)
		if newImage.getHeader("OBJECT") is None: continue 
		if (objectName == str(newImage.getHeader("OBJECT"))): objectFITSFiles.append(f)
		fileDB.addItem({'object': str(newImage.getHeader("OBJECT")), 'filename': f})
	
	fileDB.save()
	
	
