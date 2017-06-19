import os

class filedb:
	def __init__(self, workingpath='.', filename = 'objectdb.csv', debug = False):
		self.filename = os.path.join(workingpath, filename)
		self.debug = debug
		self.data = []
		
	def load(self):
		filename = self.filename
		if self.debug: print("Loading file db from ", filename)
		try:
			dbFile = open(filename, 'rt')
			for f in dbFile:
				items = f.strip().split(',')
				objectname = items[0].strip()
				filename = items[1].strip()
				date = float(items[2].strip())
				record = { 'object': objectname, 'filename': filename, 'date': date }
				self.data.append(record)
			dbFile.close()
		except IOError as e:
			if self.debug: print("Could not load existing data from %s"%filename)
		
		return
		
		
	def checkNullObjects(self):
		for s in self.data:
			print(s)
	
	def getFilesDatesFor(self, objectName):
		filelist = []
		dateList = []
		for d in self.data:
			if d['object'] == objectName: 
				filelist.append(d['filename'])
				dateList.append(d['date'])
		return filelist, dateList
	
	def getNewFilenames(self, filenamelist):
		newNames = []
		existingNames = [d['filename'] for d in self.data]
		for f in filenamelist:
			if f not in existingNames: newNames.append(f)
		return newNames
			
	def save(self):
		filename = self.filename
		if self.debug: print("Saving file db to ", filename)
		dbFile = open(filename, 'wt')
		for d in self.data:
			dbFile.write("%s, %s, %7.7f\n"%(d['object'], d['filename'], d['date']))
		dbFile.close()
	
	def addItem(self, item):
		self.data.append(item)
		
	def clean(self):
		try:
			os.remove(self.filename)
		except OSError:
			if self.debug: print("Could not remove the fileDB file.")
			
