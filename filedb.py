import os

class filedb:
	def __init__(self, filename = 'objectdb.csv', debug = False):
		self.filename = filename
		self.debug = debug
		self.data = []
		
	def load(self, path = "."):
		filename = os.path.join(path, self.filename)
		if self.debug: print "Loading file db from ", filename
		try:
			dbFile = open(filename, 'rt')
			for f in dbFile:
				items = f.strip().split(',')
				objectname = items[0].strip()
				filename = items[1].strip()
				record = { 'object': objectname, 'filename': filename }
				self.data.append(record)
			dbFile.close()
		except IOError as e:
			if self.debug: print "Could not load existing data"
		
		return
	
	def getNewFilenames(self, filenamelist):
		newNames = []
		existingNames = [d['filename'] for d in self.data]
		for f in filenamelist:
			if f not in existingNames: newNames.append(f)
		return newNames
			
	def save(self, path = "."):
		filename = os.path.join(path, self.filename)
		print "Saving file db to ", filename
		dbFile = open(filename, 'wt')
		for d in self.data:
			dbFile.write("%s, %s\n"%(d['object'], d['filename']))
		dbFile.close()
	
	def addItem(self, item):
		self.data.append(item)
