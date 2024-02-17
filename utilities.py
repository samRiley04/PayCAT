from tkinter import Tk     
from tkinter.filedialog import askopenfilename
import locale
locale.setlocale(locale.LC_ALL, '')
import json
from datetime import datetime

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

# In the format DD-MM-YYYY (which aren't easily sortable with native list.sort())
def sortDateStrings(datesList):
	# This feels so wasteful ahahahha
	tempList = []
	for x in datesList:
		tempList.append(datetime.strptime(x, "%d-%m-%Y"))
	tempList.sort()
	returnList = []
	for x in tempList:
		returnList.append(x.strftime("%d-%m-%Y"))
	return returnList

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

# These values defined here as I may want to change them for readability
SHIFT_MISSING = "Shift missing"
SHIFT_MISSING_D = "There is a shift missing on {date}."

PAY_RATE = "Pay rate different"
PAY_RATE_D = "The pay rate is different for {hourtype} on this date. Have you entered your base rate correctly in the config settings?"

HOURS_WORKED = "Hours worked different"
HOURS_WORKED_D = "The hours worked is different for {hourtype} on this date."

HOUR_TYPE = "Hour types different"
HOUR_TYPE_D = "{hourtype} is not listed in both files for this date."

DAY_TOTAL = "Day total different"
DAY_TOTAL_D = ""

def findDiscrepancies(compareList):
	debug = True
	discrepancies = {}
	datesLeft = compareList[0]["data"]
	datesRight = compareList[1]["data"]

	if len(compareList) != 2:
		raise ValueError("compareList not in correct format. Length of list is too long: length "+str(len(compareList)))

	#Create the master dates list (super set of both date lists)
	masterDatesList = []
	for date in list(datesLeft.keys()):
		masterDatesList.append(date)
	for date in list(datesRight.keys()):
		masterDatesList.append(date)
	#uniquify all keys and then sort them.
	masterDatesList = sortDateStrings(list(dict.fromkeys(masterDatesList)))
	if debug:
		print(json.dumps(masterDatesList, indent=2))

	for givenDate in masterDatesList:
		# Look for SHIFT MISSING?
		if not (givenDate in datesLeft and givenDate in datesRight):
			badges = []
			highlights = []
			badges.append({
				SHIFT_MISSING : SHIFT_MISSING_D.format(date=givenDate)
			})
			badgesAndHighlights = {
				"badges": badges,
				"highlights": highlights
			}
			discrepancies.update({
				givenDate: badgesAndHighlights
			})
			continue
			# Because if the shift is missing, doesn't matter if there are other errors (there will be)

		# Now look for the other discrepancy types by iterating a master list of hours-types
		masterHoursTypesList = []
		for entry in datesLeft[givenDate]:
			masterHoursTypesList.append(entry["description"])
		for entry in datesRight[givenDate]:
			masterHoursTypesList.append(entry["description"])
		masterHoursTypesList = list(dict.fromkeys(masterHoursTypesList))
		if debug:
			print(givenDate+" masterHoursTypesList: " + str(masterHoursTypesList))

		badges = []
		highlights = []
		for hourType in masterHoursTypesList:
			# check HOUR TYPES DIFFERENT?
			leftValues = None
			rightValues = None
			for x in datesLeft[givenDate]:
				if hourType.strip() == x["description"].strip():
					leftValues = x.copy()
					break
			for x in datesRight[givenDate]:
				if hourType.strip() == x["description"].strip():
					rightValues = x.copy()
					break
			if (leftValues is None or rightValues is None):
				badges.append({
					HOUR_TYPE:HOUR_TYPE_D.format(hourtype=hourType)
				})
				highlights.append({
					hourType:"description"
				})
				continue
				#Again, because one list is missing this hour-type, just move on as it will definitely have other errors regarding rate/amount

			# check the other descrepancy types.
			# PAY RATE DIFFERENT
			try:
				if not (float(leftValues["rate"]) == float(rightValues["rate"])):
					badges.append({
						PAY_RATE:PAY_RATE_D.format(hourtype=hourType)
					})
					highlights.append({
						hourType:"rate"
					})
			except KeyError:
				pass
			try:
				if not (float(leftValues["units"]) == float(rightValues["units"])):
					badges.append({
						HOURS_WORKED:HOURS_WORKED_D.format(hourtype=hourType)
					})
					highlights.append({
						hourType:"units"
					})
			except KeyError:
				pass
			try:
				if not (float(leftValues["amount"]) == float(rightValues["amount"])):
					#Don't add a badge for this, it's implied to the user if units/rate are different.
					#Still highlight it though:
					highlights.append({
						hourType:"amount"
					})
			except KeyError:
				pass
		
		# Add the badges and highlights for this date (if there are any).
		if not (badges == []):
			toAdd = {
				"badges": badges,
				"highlights": highlights
			}
			discrepancies.update({
				givenDate:toAdd
			})

	if debug:
		print("discrepancies")
		print(json.dumps(discrepancies, indent=2))
	return discrepancies





