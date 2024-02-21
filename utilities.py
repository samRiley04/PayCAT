from tkinter import Tk     
from tkinter.filedialog import askopenfilename
import locale
locale.setlocale(locale.LC_ALL, '')
import json
from datetime import datetime, timedelta

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

# These values defined here as I may want to change them for readability

DATE_RANGE_TOO_LONG = "The date range selected for '{filename}' is more than a fortnight ({startdate} to {enddate}). Please be aware overtime calculations will be incorrect."
DATES_NOT_ALIGNED = "The dates included in '{filename}' ({sd1} to {ed1}) and '{filename2}' ({sd2} to {ed2}) do not align."

SHIFT_MISSING = "Shift missing"
SHIFT_MISSING_D = "There is a shift missing on {date}."

PAY_RATE = "Pay rate different"
PAY_RATE_D = "The pay rate is different for {hourtype} on this date. Have you entered your base rate correctly in the config settings?"

HOURS_WORKED = "Hours worked different"
HOURS_WORKED_D = "The hours worked is different for {hourtype} on this date."

HOURS_NEGATIVE = "Negative hours"
HOURS_NEGATIVE_D = "The hours for {hourtype} on this date have been entered as a negative number. You should check if this is correct."

HOUR_TYPE = "Hour types different"
HOUR_TYPE_D = "{hourtype} is not listed in both files for this date."

DAY_TOTAL = "Day total different"
DAY_TOTAL_D = ""

def findDiscrepancies(compareList):
	debug = True
	discrepancies = {}
	globalDiscrepancies = []
	datesLeft = compareList[0]["data"]
	datesRight = compareList[1]["data"]

	if len(compareList) != 2:
		raise ValueError("compareList not in correct format. Length of list is too long: length "+str(len(compareList)))

	#Check for global discrepancies (roster dates more than 14 days in range, or dates not matching)
	storeList = []
	for side in compareList:
		letsCheck = []
		for date in side["data"]:
			letsCheck.append(datetime.strptime(date, "%d-%m-%Y"))
		letsCheck.sort()

		if not storeList == [] and not (storeList[0] == letsCheck[0] and storeList[-1] == letsCheck[-1]): #If the store list is defined (checking the second comparelist), and range of both lists isn't identical:
			globalDiscrepancies.append(DATES_NOT_ALIGNED.format(filename=compareList[0]["name"],
																filename2=compareList[1]["name"],
																sd1=storeList[0].strftime("%d-%m-%Y"),
																ed1=storeList[-1].strftime("%d-%m-%Y"),
																sd2=letsCheck[0].strftime("%d-%m-%Y"),
																ed2=letsCheck[-1].strftime("%d-%m-%Y")))
		else:
			storeList = letsCheck.copy()
		if side["name"].endswith(".pdf"): 
			continue #doesn't matter if payslips cover more than 14 days - user cannot control this, so why tell them?
		if (letsCheck[-1] - letsCheck[0]) > timedelta(days=14):
			globalDiscrepancies.append(DATE_RANGE_TOO_LONG.format(filename=side["name"], startdate=letsCheck[0].strftime("%d-%m-%Y"), enddate=letsCheck[-1].strftime("%d-%m-%Y")))

		print(storeList)
		print(letsCheck)

			


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
			# Before we continue, quick check for any cardinal sins
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
				if float(leftValues["units"]) < 0:
					badges.append({
						HOURS_NEGATIVE:HOURS_NEGATIVE_D.format(hourtype=hourType)
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
		print(globalDiscrepancies)
	return discrepancies, globalDiscrepancies





