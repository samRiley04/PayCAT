from tkinter import Tk     
from tkinter.filedialog import askopenfilename
import locale
locale.setlocale(locale.LC_ALL, '')

# Opens a file selector. Then, returns the path to that file to the original main process using a Queue.
#Unfortunately neccessary to create an entire subprocess just to use tkinter (*must* be run in the main process.)
def filePicker(q):
	root = Tk()
	root.withdraw()
	file_path = askopenfilename()
	q.put(file_path)

# Because ingestRoster() is fed into analyseRoster(), and it doesn't know a few things about the payslip data, it must be wrapped with a few more pieces on information before being stored.
def deepSumAmounts(dataDict):
	sumAmt = 0
	for date, hoursList in dataDict.items():
		for hoursEntry in hoursList:
			sumAmt+=float(hoursEntry["amount"])
	return locale.currency(sumAmt, symbol=False, grouping=True)


"""
	REDUNDANT - don't need to uniqufy these anymore as data is stored under IDs now.
	if fileNameShort in shlf:
		#Attempt to unique-ify the name. This may be unsuccessful, thus the second loop check.
		filesTrueName = fileNameShort[:-4] #trim the .pdf
		fileNameShort = filesTrueName + "(1).pdf"
		indx = 1
		#Did that unique-ifying work?
		while fileNameShort in shlf:
			#No? Ok keep iterating.
			indx += 1
			fileNameShort = filesTrueName + "(" + str(indx) + ").pdf"
"""