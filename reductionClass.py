import matplotlib.pyplot
import fitsClasses
import numpy, sys
import linearShift, generalUtils
from photutils import daofind
from photutils import DAOStarFinder
from astropy.stats import median_absolute_deviation as mad
from astropy.stats import sigma_clipped_stats
from scipy import ndimage

class frameObject:
	def __init__(self):
		self.name = 'blank frame'
		self.size = None
		self.imageData = None
		self.rawFrames = []
		self.sources = None
		
	def findSources(self):
		bkg_sigma = 1.48 * mad(self.imageData)
		mean, median, std = sigma_clipped_stats(self.imageData, sigma=3.0, iters=5)    
		# sources = daofind(self.imageData, fwhm=4.0, threshold=3*bkg_sigma)
		# print(sources)
		daotool = DAOStarFinder(fwhm=3.0, threshold=5.*std)
		sources = daotool.find_stars(self.imageData)   
		# print(sources)
		sources = sorted(sources, key=lambda x: x['flux'], reverse=True)
		self.sources = sources[:30]
		return self.sources

class reductionObject:
	def __init__(self, targetName = 'unknown', debug = False):
		self.debug = debug
		self.rawFrames = []
		self.targetName = targetName
		self.sourceFrames = []
		
	def info(self):
		retStr = "Reduction object:\n-----------------\n"
		retStr+= "target: %s\n"%self.targetName
		retStr+= "raw frames: %d\n"%len(self.rawFrames)
		return retStr
	
	def setRawFrameInfo(self, frames, dates):
		self.rawFrames = [ {'filename': f, 'date': p} for f, p in zip(frames, dates)]
		
	def sortRaw(self):
		self.rawFrames = sorted(self.rawFrames, key=lambda x: x['date'])
		
	def computeMedianImage(self, start, end, tweak = False):
		size = end - start
		print('Computing a median image starting with: %d and going to: %d'%(start, end))
		if (size%2)==0:
			print("I prefer to compute the median from an odd number of data points. You specified %d."%size)
			return
		imageArray = []
		sourceFrames = []
		if tweak:
			recordShifts = []
		for i in range(size): 
			frameIndex = start + i
			incrementalFrame = fitsClasses.fitsObject(debug = self.debug)
			incrementalFrame.initFromFITSFile(self.rawFrames[frameIndex]['filename'])
			sourceFrames.append(self.rawFrames[frameIndex]['filename'])
			incrementalFrame.getImageData()
			imageArray.append(incrementalFrame.fullImage['data'])
			thisImage = frameObject()
			thisImage.imageData = imageArray[-1]
			sys.stdout.write("\rLoading: %d"%(frameIndex))
			if tweak:
				if self.referenceFrame is not None: 
					referenceSources = self.referenceFrame.sources
					if referenceSources is None:
						self.referenceFrame.findSources()
					sources = thisImage.findSources()
					refCat = [[s['xcentroid'], s['ycentroid']] for s in referenceSources]
					thisCat = [[s['xcentroid'], s['ycentroid']] for s in sources]
					psize  = 0.5
					fwhm   = 4.
					dmax   = 30.
					mmax   = 30.
					(gaussImage, xp, yp, xr, yr) = linearShift.vimage(refCat, thisCat, dmax, psize, fwhm)
					#(nmatch, inds) = ultracam_shift.match(prevCatalog, newCatalog, xp, yp, mmax)
					thisImage.imageData = ndimage.interpolation.shift(thisImage.imageData, (-1.0*yr, -1.0*xr), order = 4 )
					imageArray[-1] = thisImage.imageData
					recordShifts.append({'x': xr, 'y': yr, 'frame': i})
					if tweak: sys.stdout.write("  shift applied: %f, %f    "%(-xr, -yr))

				else:
					print("There is no reference frame to determine sources for position tweaking.")
					
			sys.stdout.flush()
	
		print()
		medianImage = numpy.median(imageArray, axis=0)
		self.medianImage = frameObject()
		self.medianImage.imageData = medianImage
		self.medianImage.name = "Median image generated from frames %d to %d"%(start, start+size)
		if tweak: self.medianImage.name+= "[position tweaked]"
		self.medianImage.sourceFrames = sourceFrames
		if tweak: return self.medianImage, recordShifts
		else: return self.medianImage
		
	
	def computeMeanFrame(self, start, stop, tweak = False):
		print('Computing a mean image starting with: ', start)
		firstFrame = fitsClasses.fitsObject(debug = self.debug)
		firstFrame.initFromFITSFile(self.rawFrames[start]['filename'])
		firstFrame.getImageData()
		
		if tweak:
			recordShifts = []
		
		meanImage = numpy.zeros(firstFrame.size)
		sourceFrames = []
		meanImage+= numpy.array(firstFrame.fullImage['data'])
		for i in range(start+1, stop+1):
			incrementalFrame = fitsClasses.fitsObject(debug = self.debug)
			incrementalFrame.initFromFITSFile(self.rawFrames[i]['filename'])
			sourceFrames.append(self.rawFrames[i]['filename'])
			incrementalFrame.getImageData()
			thisImage = frameObject()
			thisImage.imageData = incrementalFrame.fullImage['data']
					
			if tweak:
				if self.referenceFrame is not None: 
					referenceSources = self.referenceFrame.sources
					if referenceSources is None:
						self.referenceFrame.findSources()
					sources = thisImage.findSources()
					refCat = [[s['xcentroid'], s['ycentroid']] for s in referenceSources]
					thisCat = [[s['xcentroid'], s['ycentroid']] for s in sources]
					psize  = 0.5
					fwhm   = 4.
					dmax   = 30.
					mmax   = 30.
					(gaussImage, xp, yp, xr, yr) = linearShift.vimage(refCat, thisCat, dmax, psize, fwhm)
					#(nmatch, inds) = ultracam_shift.match(prevCatalog, newCatalog, xp, yp, mmax)
					thisImage.imageData = ndimage.interpolation.shift(thisImage.imageData, (-1.0*yr, -1.0*xr), order = 4 )
					recordShifts.append({'x': xr, 'y': yr, 'frame': i})
				else:
					print("There is no reference frame to determine sources for position tweaking.")
		
			meanImage+= thisImage.imageData
		
		
			sys.stdout.write("\rAdding: [%d]  %d"%(i, stop))
			if tweak: sys.stdout.write("  shift applied: %f, %f    "%(-xr, -yr))

			sys.stdout.flush()
		
		
		print()
		self.meanImage = meanImage / (stop - start)
		self.meanImage = frameObject()
		self.meanImage.imageData = meanImage
		self.meanImage.name = "Mean image generated from frames %d to %d"%(start, stop)
		if tweak: self.meanImage.name+= " [tweak applied]"
		self.meanImage.sourceFrames = sourceFrames
		if tweak: return self.meanImage, recordShifts
		else: return self.meanImage
		
		
	def plotFrame(self, number):
		image = fitsClasses.fitsObject(debug=self.debug)
		filename = self.rawFrames[number]['filename']
		image.initFromFITSFile(filename)
		image.getImageData()
		imageData = image.getBoostedImage()
		matplotlib.pyplot.figure(figsize=(8, 8/1.618))
		matplotlib.pyplot.xlabel("X (pixels)", size = 12)
		matplotlib.pyplot.ylabel("Y (pixels)", size = 12)
		imgplot = matplotlib.pyplot.imshow(imageData)
		matplotlib.pyplot.draw()
		matplotlib.pyplot.show()
		
		return
