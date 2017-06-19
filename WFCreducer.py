#!/usr/bin/env python3
import argparse, re, os, json, sys
import fitsClasses, filedb, reductionClass, generalUtils
import plotImages
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Reads FITS files produced by the Wide Field Camera and attempts an online reduction.')
	parser.add_argument('--datapath', type=str, default = '.', help='Path where the FITS files are. Default: current directory.')
	parser.add_argument('--workingpath', type=str, default = '.', help='Path for the working and reduction files. Default: current directory.')
	parser.add_argument('object', type=str, help='Object name as specified in the FITS header.')
	parser.add_argument('--debug', action='store_true', help='Print some extra debug information.')
	parser.add_argument('-R', '--recursive', action='store_true', help='Look in sub-folders too.')
	parser.add_argument('--clean', action='store_true', help='Clean out working files and generate the reduction files all over again.')
	args = parser.parse_args()
	
	targetName = args.object
	datapath = args.datapath
	workingpath = args.workingpath
	debug = args.debug
	
	fileDB = filedb.filedb(debug = debug, workingpath = workingpath)
	
	if args.clean:
		fileDB.clean()
		
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
		print("%d FITS files in the directory %s"%(len(FITSFilenames), resolvedPath))
		if not args.recursive: break
	
	FITSFilenames = sorted(FITSFilenames)	
	
	fileDB.load()
	
	newFiles = fileDB.getNewFilenames(FITSFilenames)
			
	print("%d files are new."%len(newFiles))
	 
	objectFITSFiles = []
	for f in newFiles:
		newImage = fitsClasses.fitsObject(debug=debug)
		newImage.initFromFITSFile(f)
		if newImage.getHeader("OBJECT") is None: 
			objectName = 'JUNK'
			# Try to get the object name from the filename
			if targetName in f:
				objectName = targetName
		else:  
			objectName = str(newImage.getHeader("OBJECT"))
		try:
			dateObs = float(newImage.getHeader("JD"))
		except TypeError:
			if debug: print("Warning: Could not read the date for", f)
			dateObs = 0
		objectFITSFiles.append(f)
		fileDB.addItem({'object': objectName, 'filename': f, 'date': dateObs})
	
	fileDB.checkNullObjects()
	
	fileDB.save()
	
	# Start the reduction
	print("Starting the reduction.")
	reduction = reductionClass.reductionObject(targetName, debug = debug)
	rawFrames, rawDates = fileDB.getFilesDatesFor(targetName)
	reduction.setRawFrameInfo(rawFrames, rawDates)
	reduction.sortRaw()
	print(reduction.info())
	referenceFrame = reduction.computeMeanFrame(50, 70, tweak = False)
	reduction.referenceFrame = referenceFrame
	referenceFrame.findSources()
	#reduction.computeMedianImage(20, 31)
	#plotImages.plotImage(reduction.medianImage, boost=True)
	meanImagePlot = plotImages.plotImage(reduction.meanImage, boost=True)
	plotImages.plotSources(reduction.referenceFrame.sources, meanImagePlot)
	
	newMeanImage, shifts = reduction.computeMeanFrame(1, 100, tweak = True)
	plotImages.plotImage(newMeanImage, boost=True)
	newMeanImage2, shifts = reduction.computeMeanFrame(101, 200, tweak = True)
	plotImages.plotImage(newMeanImage2, boost=True)
	# newMedianImage, shifts = reduction.computeMedianImage(1, 100, tweak = True)
	# plotImages.plotImage(newMedianImage, boost=True)
	newMedianImage, shifts = reduction.computeMedianImage(101, 200, tweak = True)
	plotImages.plotImage(newMedianImage, boost=True)
	
	generalUtils.query_yes_no("Continue?")
