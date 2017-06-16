import matplotlib.pyplot
import numpy

def boostImage(imageData, lo=20, hi=99):
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

def plotImage(image, boost=False):
	imageData = image.imageData
	imageTitle = image.name
	if boost: imageData = boostImage(imageData)
	figure = matplotlib.pyplot.figure(figsize=(8, 8/1.618))
	matplotlib.pyplot.xlabel("X (pixels)", size = 12)
	matplotlib.pyplot.ylabel("Y (pixels)", size = 12)
	figure.canvas.set_window_title(imageTitle)
	imgplot = matplotlib.pyplot.imshow(imageData)
	matplotlib.pyplot.draw()
	matplotlib.pyplot.show(block=False)
	return figure
	
def plotSources(sources, figure):
	matplotlib.pyplot.figure(figure.number)
	xpos = [ s['xcentroid'] for s in sources]
	ypos = [ s['ycentroid'] for s in sources]
	matplotlib.pyplot.scatter(xpos, ypos, color = 'r', alpha=0.5)
	matplotlib.pyplot.draw()
	matplotlib.pyplot.show(block = False)
		

