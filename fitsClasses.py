import astropy, sys, numpy, scipy
import scipy.misc
from astropy.io import fits
from PIL import Image,ImageDraw,ImageFont

class fitsObject:
	def __init__(self, debug = False):
		self.filename = None
		self.boostedImageExists = False
		self.allHeaders = {}
		self.fullImage = {}
		self.debug = debug
		
	def initFromFITSFile(self, filename):
		images = []
		try:
			hdulist = fits.open(filename)
			if self.debug: print "Info: ", hdulist.info()
			# card = hdulist[0]
			for h in hdulist:
				if type(h.data) is numpy.ndarray:
					imageObject = {}
					imageObject['data'] = h.data
					imageObject['size'] = numpy.shape(h.data)
					if len(imageObject['size'])<2:
						if self.debug: print "Data is one-dimensional. Not valid."
						return False
					images.append(imageObject)
					if self.debug: print("Found image data of dimensions (%d, %d)"%(imageObject['size'][0], imageObject['size'][1]))
				else:
					if self.debug: print "This card has no image data"
					continue                 # This card has no image data
			# Grab all of the FITS headers I can find
			for card in hdulist:
				for key in card.header.keys():
					self.allHeaders[key] = card.header[key]
			hdulist.close(output_verify='ignore')
		except astropy.io.fits.verify.VerifyError as e:
			
			print "WARNING: Verification error", e
			
		except Exception as e: 
			print "Unexpected error:", sys.exc_info()[0]
			print e
			print "Could not find any valid FITS data for %s"%filename
			return False
		
		self.filename = filename
		if len(images)==0:
			if self.debug: print "Could not find any valid FITS data for %s"%filename
			return False
		if len(images)>1:
			self.combineImages(images)
		else:
			self.fullImage = images[0]
			self.size = numpy.shape(self.fullImage['data'])
		return True
		
	def getHeader(self, key):
		if key in self.allHeaders.keys():
			return self.allHeaders[key] 
			
	def combineImages(self, images):
		if self.debug: print "Combining %d multiple images."%len(images)
		WFC = False
		try:
			instrument = self.allHeaders['INSTRUME']
			if self.debug: print "Instrument detected:", instrument
			WFC = True
		except KeyError:
			pass
		
		# Reduce the images sizes by 1/4	
		for num, i in enumerate(images):
			percent = 25
			if self.debug: print "Shrinking image %d by %d percent."%(num, percent)
			i['data'] = scipy.misc.imresize(self.boostImageData(i['data']), percent)
			i['size'] = numpy.shape(i['data'])
			if self.debug: print "New size:", i['size']
			
		if WFC:
			# Custom code to stitch the WFC images together
			CCD1 = images[0]
			CCD2 = images[1]
			CCD3 = images[2]
			CCD4 = images[3]
			width = CCD1['size'][1]
			height = CCD1['size'][0] 
			fullWidth = width + height
			fullHeight = 3 * width
			if self.debug: print "WFC width", fullWidth, "WFC height", fullHeight
			fullImage = numpy.zeros((fullHeight, fullWidth))
			CCD3data = numpy.rot90(CCD3['data'], 3)
			fullImage[0:width, width:width+height] = CCD3data
			CCD2data = CCD2['data']
			fullImage[width:width+height, 0:width] = CCD2data
			CCD4data = numpy.rot90(CCD4['data'], 3)
			fullImage[width:2*width, width:width+height] = CCD4data
			CCD1data = numpy.rot90(CCD1['data'], 3)
			fullImage[2*width:3*width, width:width+height] = CCD1data
			fullImage = numpy.rot90(fullImage, 2)
		else:
			totalWidth = 0
			totalHeight = 0
			for i in images:
				totalWidth+= i['size'][1]
				totalHeight+=i['size'][0]
			if self.debug: print "potential width, height", totalWidth, totalHeight 
			if totalWidth<totalHeight:
				if self.debug: print "Stacking horizontally"
				maxHeight = 0
				for i in images:
					if i['size'][0]>maxHeight: maxHeight = i['size'][0]
				fullImage = numpy.zeros((maxHeight, totalWidth))
				if self.debug: print "Full image shape", numpy.shape(fullImage)
				segWstart = 0
				segHstart = 0
				for num, i in enumerate(images):
					segWidth = i['size'][1] 
					segHeight = i['size'][0]
					segWend = segWstart + segWidth
					segHend = segHstart + segHeight
					fullImage[segHstart:segHend, segWstart: segWend] = i['data']
					segWstart+= segWidth
		
		
		self.fullImage['data'] = fullImage
		self.fullImage['size'] = numpy.shape(fullImage)
		self.size = numpy.shape(fullImage)
		if self.debug: print "Final size:", self.size
		
	def boostImageData(self, imageData):
		""" Returns a normalised array where lo percent of the pixels are 0 and hi percent of the pixels are 255 """
		hi = 99
		lo = 20
		data = imageData
		max = data.max()
		dataArray = data.flatten()
		pHi = numpy.percentile(dataArray, hi)
		pLo = numpy.percentile(dataArray, lo)
		range = pHi - pLo
		scale = range/255
		data = numpy.clip(data, pLo, pHi)
		data-= pLo
		data/=scale
		return data
		
	
	def getBoostedImage(self):
		""" Returns a normalised array where lo percent of the pixels are 0 and hi percent of the pixels are 255 """
		hi = 99
		lo = 20
		imageData = self.fullImage['data']
		data = numpy.copy(self.fullImage['data'])
		max = data.max()
		dataArray = data.flatten()
		pHi = numpy.percentile(dataArray, hi)
		pLo = numpy.percentile(dataArray, lo)
		range = pHi - pLo
		scale = range/255
		data = numpy.clip(data, pLo, pHi)
		data-= pLo
		data/=scale
		self.boostedImage = data
		self.boostedImageExists = True
		return data
		
	def writeAsPNG(self, boosted=False, filename = None):
		imageData = numpy.copy(self.fullImage['data'])
		if boosted==True:
			if not self.boostedImageExists: imageData = self.getBoostedImage()
			else: imageData = self.boostedImage
		imgData = numpy.rot90(imageData, 3)
		imgSize = numpy.shape(imgData)
		imgLength = imgSize[0] * imgSize[1]
		testData = numpy.reshape(imgData, imgLength, order="F")
		img = Image.new("L", imgSize)
		palette = []
		for i in range(256):
			palette.extend((i, i, i)) # grey scale
			img.putpalette(palette)
		img.putdata(testData)
		
		if filename==None:
			outputFilename = changeExtension(self.filename, "png")
		else:
			outputFilename = filename
			
		if self.debug: print ("Writing PNG file: " + outputFilename) 
		img.save(outputFilename, "PNG", clobber=True)
		
	def createThumbnail(self, filename = None, size=128):
		if not self.boostedImageExists: imageData = self.getBoostedImage()
		else: imageData = self.boostedImage
		
		imgData = numpy.rot90(imageData, 3)
		imgSize = numpy.shape(imgData)
		imgLength = imgSize[0] * imgSize[1]
		testData = numpy.reshape(imgData, imgLength, order="F")
		img = Image.new("L", imgSize)
		palette = []
		for i in range(256):
			palette.extend((i, i, i)) # grey scale
			img.putpalette(palette)
		img.putdata(testData)
		thumbnailSize = (size, size)
		img.thumbnail(thumbnailSize, Image.ANTIALIAS)
		if filename==None:
			outputFilename = "thumb_" + changeExtension(self.filename, "png")
		else:
			outputFilename = filename
		
		if self.debug: print ("Writing thumbnail file: " + outputFilename) 
		img.save(outputFilename, "PNG", clobber=True)
