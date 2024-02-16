import PyPDF2
import openpyxl
from openpyxl import load_workbook
import yaml
from datetime import datetime, timedelta
from datetime import time
from dateutil import parser
import json
import re
import custom_exceptions as ex

#Alerts - in the form [priority (HI/MED/LO), title, body]
alerts = []

#Descriptions dict - to aid with payslip ingestion. List of known possible descriptions.
descShortlist = [
	"BASE HOURS",
	"PUBLIC HOLIDAY 1.5",
	"PROFESSIONAL DEVT ALLOW",
	"SMART SALARY SP FIXED",
	"PENALTIES AT 25%",
	"PENALTIES AT 20%",
	"PENALTIES AT 75%",
	"OVERTIME @ 1.5",
	"MEAL - BREAKFAST MED PRAC",
	"MEAL - DINNER MED PRACT",
	"ANNUAL LEAVE"
]

# Returns the number of hours represented by a string of a given time range
# e.g. '0800-1800' returns 10
def parseHours(string):
	s = None
	try:
		# This regular expression makes me aroused
		# accepts (HHHH or (1 to 9)HH or 000)-(HHHH or (1 to 9)HH or 000)
		# or
		# accepts (HH:HH or (1 to 9):HH or 0:00)-(HH:HH or (1 to 9):HH or 0:00)
		s = re.search(r'(\d{2}(:?)\d{2}|[1-9](:?)\d{2}|0(:?)00)\s*-\s*(\d{2}(:?)\d{2}|[1-9](:?)\d{2}|0(:?)00)', string)
	except TypeError:
		pass
	if not s is None:
		times = s.group().replace(' ','').replace(":","").split("-")
		outputStr = ""
		# Have to clone the array else it gives errors.
		for indx, t in enumerate(times.copy()):
			# Regex has ensured this is safe to do - if time has no leading zero, add it. (required for datetime parsing)
			if len(t) == 3:
				times[indx] = "0"+times[indx]
		"""
		# Don't calculate the total hours yet		
		dif = datetime.strptime(times[1], "%H%M") - datetime.strptime(times[0], "%H%M")
		return float((dif.seconds/60)/60)
		"""
		#May not be the most elegant way to have done this but so be it.
		return times[0] + "-" + times[1]
	else:
		return None

def parseDate(string):
	s = None
	try:
		# YYYY-MM-DD or XX-XX-XX or DD-MM-YYYY
		s = re.search(r'(\d{4}[-/\. ]\d{2}[-/\. ]\d{2})|(\d{2}[-/\. ]\d{2}[-/\. ](\d{4}|\d{2}))', string)
	except TypeError:
		print
	if not s is None:
		return s.group()
	else:
		return None

def ingestTypeA(sheet, findName, debug):
	outputDict = {}
	return outputDict

def ingestTypeB(sheet, findName, debug):
	outputDict = {}
	tempDates = {}
	# find DATE CELLS
	# AND check validity of DATES simultaneously
	for row in sheet.iter_rows():
		for cell in row:
			# If the cell isn't empty
			if not (cell.value is None):
				dateAttempt = parseDate(str(cell.value))
				#parseDate returns None if it doesn't match a date.
				# Then check if it's a valid bonafide date. (check down first, if that fails, laterally)
				if not (dateAttempt is None):
					if dateValidTypeB(cell, sheet):
						# Copy whole cell object so can access row/col easier.
						tempDates.update({
							str(dateAttempt):cell
						})
					elif debug:
						print("DISCARDING potential date: " + dateAttempt)
	if len(tempDates) == 0:
		#Found no recognisable dates in the roster
		raise ex.NoRecognisedDates()
	if debug:
		print("tempDates: "+ str(tempDates))
	# find NAME COLS
	tempNameRows = []
	for col in sheet.iter_cols():
		for cell in col:
			if cell.value == findName:
				tempNameRows.append(cell.row)
	if len(tempNameRows) == 0:
		# Did not find a name.
		raise ex.NameNotFound()
	# create outputDict
	# Remember tempDates contains {DATES:cells}
	if debug:
		print("tempNameRows: " + str(tempNameRows))
	for dateKey in tempDates:
		# Find out if the nameRow is the closest row AFTER the date in question (prevent doubling up due to vertical roster stacking)
		closestRow = max(tempNameRows)
		for row in tempNameRows:
			rowDif1 = row - int(tempDates[dateKey].row)
			rowDif2 = closestRow - int(tempDates[dateKey].row)
			# >0 ensures the row is AFTER the date in question.
			if (rowDif1 < rowDif2) and (rowDif1 > 0):
				closestRow = row
			#if debug:
				#print("attempted row: " + str(row)+". dif was "+str(rowDif1) + " and now closest row is " + str(closestRow))

		if debug:
			print("col: "+ tempDates[dateKey].column_letter + " | row: "+ str(closestRow))
		hrs = parseHours(sheet[str(tempDates[dateKey].column_letter)+str(closestRow)].value)
		if not (hrs is None):
			# Only update the dict if hours worked is a value
			outputDict.update({dateKey:hrs})
	if debug:
		print("Pre-cull outputDict: ")
		print(json.dumps(outputDict, indent=4))
	return outputDict

def ingestTypeC(sheet, findName, debug):
	outputDict = {}
	tempNameCols = []
	# find NAME CELLS
	# AND check validity of NAMES simultaneously
	for row in sheet.iter_rows():
		for cell in row:
			# If the cell isn't empty
			if not (cell.value is None) and (cell.value == findName) and not (cell.column_letter in tempNameCols):
				tempNameCols.append(cell.column_letter)
	if len(tempNameCols) == 0:
		#Found no recognisable name in the roster
		raise ex.NameNotFound()
	if debug:
		print("tempNameCols: " + str(tempNameCols))
	# find DATE ROWS (include the dates as well {"2":"2023-08-22"})
	tempDates = {}
	for col in sheet.iter_cols():
		for cell in col:
			if not (cell.value is None):
				dateAttempt = parseDate(str(cell.value))
				if not (dateAttempt is None):
					if dateValidTypeC(cell, sheet):
						tempDates.update({
							cell.row:dateAttempt
							})
					elif debug:
						print("DISCARDING potential date: " + dateAttempt)
	if len(tempDates) == 0:
		# Did not find a name.
		raise ex.NoRecognisedDates()
	if debug:
		print("tempDates: " + str(tempDates))
	# create outputDict
	# Remember tempNameCols contains [col, col]
	# Iterate through each name, then collect all the date-rows below it
	for col in tempNameCols:
		for row in tempDates:
			hrs = parseHours(sheet[str(col)+str(row)].value)
			if not (hrs is None): 
				outputDict.update({
					tempDates[row]:hrs
				})
	return outputDict

# SENSITIVITY MAY NEED TO BE TITRATED TO EFFECT in future.
def dateValidTypeA(cell, sheet):
	return True

def dateValidTypeB(cell, sheet):
	debug = False
	counter = 0
	# After marginValue number of cells that dont contain valid strings, consider this date INVALID.
	marginValue = 4
	# CHECK FOR HOURS BELOW
	# Create a range and iterate (next #marginValue cells not including the date cell itself.)
	for rowDown in sheet[cell.column_letter+str(cell.row+1):cell.column_letter+str(cell.row+marginValue)]:
		for cellDown in rowDown:
			counter += 1
			if debug:
				print("date: " + str(cell.value) + " | checking: " + str(cellDown.value))
			if not (parseHours(cellDown.value) is None):
				# Got at least one valid string before the marginValue cutoff, so it's Valid.
				return True
			elif not (cellDown.value is None):
				# If you encounter any non-hours-like shit below, it's likely invalid
				return False
			elif counter >= marginValue:
				# Unclear if invalid (only saw empty cells)
				# CHECK FOR DATES EITHER SIDE
				# Create a range and iterate
				if cell.column == 1:
					compareLeft = "<INVALID_DATE>"
				else:
					compareLeft = str(sheet.cell(row=cell.row, column=cell.column-1).value)
				compareRight = str(sheet.cell(row=cell.row, column=cell.column+1).value)
				if debug:
					print("R: ")
					print(compareRight)
					print("L: ")
					print(compareLeft)
				# If either of left or right are valid dates.
				if (parseDate(compareLeft) or parseDate(compareRight)):
					return True
				return False

def dateValidTypeC(cell, sheet):
	debug = False
	"""
	<TEMPORARILY DISABLED to titrate sensitivity - to be considered for re-inclusion in the future if indicated>
	counter = 0
	marginValue = 4
	# CHECK FOR HOURS ON RIGHT
	# Create a range and iterate (next #marginValue cells not including the date cell itself.)
	rangeStart = sheet.cell(column=(cell.column + 1), row=cell.row).coordinate
	rangeEnd = sheet.cell(column=(cell.column + marginValue), row=cell.row).coordinate
	for colsAcross in sheet[rangeStart:rangeEnd]:
		for cellAcross in colsAcross:
			counter += 1
			if debug:
				print("date: " + str(cell.value) + " | checking: " + str(cellAcross.value))
			if not (parseHours(cellAcross.value) is None):
				# Got at least one valid string before the marginValue cutoff, so it's Valid.
				return True
			elif not (cellAcross.value is None):
				# If you encounter any non-hours-like shit below, it's likely invalid
				return False
			elif counter >= marginValue:
				# Unclear if invalid (only saw empty cells)
			"""
				# CHECK FOR DATES ABOVE/BELOW
				# Create a range and iterate
	if cell.row == 1:
		compareAbove = "<INVALID_DATE>"
	else:
		compareAbove = str(sheet.cell(row=cell.row-1, column=cell.column).value)
	compareBelow = str(sheet.cell(row=cell.row+1, column=cell.column).value)
	if debug:
		print("AB: ")
		print(compareAbove)
		print("BEL: ")
		print(compareBelow)
	# If either of above or below are valid dates.
	if (parseDate(compareAbove) or parseDate(compareBelow)):
		return True
	return False

# RETURN ERRORS
# ValueError - "employee name not found", "recognisable dates not found"
def ingestRoster(fileName, findName, rosterFormat, startDate, endDate, ignoreHidden=True, debug=False):
	outputDict = {}
	wb = load_workbook(fileName, data_only=True)
	sheet = wb.active
	try:
		if rosterFormat == "A":
			outputDict = ingestTypeA(sheet, findName, debug)
		elif rosterFormat == "B":
			outputDict = ingestTypeB(sheet, findName, debug)
		elif rosterFormat == "C":
			outputDict = ingestTypeC(sheet, findName, debug)
		else:
			#the fuck?
			raise ValueError()
	except (ValueError):
		raise ValueError("Invalid roster format: " + str(rosterFormat))
	except (ex.NameNotFound):
		raise ValueError("Found no recognisable name in the roster \'"+fileName+"\'. Is it spelled correctly?")
	except (ex.NoRecognisedDates):
		raise ValueError("Found no recognisable dates in the roster \'"+fileName+"\'.")
	#Now all the roster is ingested, trim the dict using the start/end dates.
	copy = outputDict.copy()
	for entry in copy:
		e = datetime.strptime(entry, "%Y-%m-%d")
		if not (e >= startDate and e <= endDate):
			outputDict.pop(entry)
	if outputDict == {}:
		raise ValueError("Found no recognisable dates in the roster \'"+fileName+"\'.")
	return outputDict


#print(json.dumps(ingestRoster("TESTING/OPH.xlsx", "Samuel Riley", "C", datetime.strptime("2023-02-13", "%Y-%m-%d"), datetime.strptime("2023-02-26", "%Y-%m-%d")), indent=4))


# TODO - re-write this entire function using Regex (will be a LOT shorter). I am dumb.
def ingestPDF(fileName):
	payPeriodLength = 14
	#Payslip Dictionary (the end product of ingesting the payslip)
	psDict = {}
	with open(fileName, 'rb') as pdf:
		pdfReader = PyPDF2.PdfReader(pdf)
		pageOfInterest = pdfReader.pages[1].extract_text().split('\n')
		LINELIMITER = 0
		# PAGE TWO ----
		for line in pageOfInterest:
			#If this line starts with a number (the only lines we are interested in do)
			if line[0][0].isnumeric():
				#if LINELIMITER <= 9:
				#	LINELIMITER+=1
				#else:
				#	break
				#print('DOING-------')
				# Remove all those random double sapces
				wordsList = " ".join(line.split()).split(" ")
				#print(wordsList)
				date = ""
				description = ""
				units = ""
				rate = ""
				amount = ""

				# GO WORD BY WORD until we get our description done (requires iterating)
				for index, word in enumerate(wordsList):
					if not description == "":
						# Once we have our description, we don't need to iterate on the list anymore.
						break

					# ?Date (and we don't already have a date stored)
					if word.replace('-','').isnumeric() and date == "":
						date = str(word)
					# ?Description
					# This one is harder
					elif word.isalpha():
						# If we already have a description, pass on.
						if not description == "":
							continue
						# Attempt to consolidate the word using known list of descriptions.
						# Iterate through the remainder of the words from where we are up to, creating a franken-word to see if it fits any known descriptions.
						frankenword = ""
						for candidate in wordsList[index:]:
							# Attempt to identify if we have reached the "units" column erroneously (check the last three charcters)
							frankenword += candidate
							if frankenword in descShortlist:
								description = frankenword
								break
							else:
								frankenword += " "
							#If we have reached and checked a number and the word still doesn't match, we have gone too far. Subtract the number and just go with the words part, must be a new term.
							#Checking for numbers AFTER the frankenword ensures that descriptions CONTAINING A NUMBER will still be stored correctly.
							#It makes having to remove the string we just added worth it.
							if candidate.replace(".","").isnumeric():
								description = frankenword[:-len(candidate)-1]
								alerts.append(["MED", "New Description", "The description \'"+description+"\' has not been encountered before. Should we record it into the dictionary?"])
								break
				# NOW COLLECT the numeric values.
				# (but first do this) If the date-entry doesn't already exist (it might), initialise it as a list.
				if not date in psDict.keys():
					psDict[date] = []

				# Two formats of payslip rows:
				# (1) DATE - DESCRIPTION - UNITS - RATE - AMOUNT
				# (2) DATE - SECOND DATE - DESCRIPTION - AMOUNT
				# Use this information to trickily collect the last data and then input it into the dict.
				if wordsList[1].count("-") == 2:
					amount = wordsList[-1]
					psDict[date].append({"description":description,
									"amount":amount})
				else:
					units = wordsList[-3]
					rate = wordsList[-2]
					amount = wordsList[-1]
					psDict[date].append({"description":description,
									"units":units,
									"rate":rate,
									"amount":amount})
		
		# NOW grab all the random info from page 1 and fill the psDict.
		
		# PAGE ONE ----
		pageOfInterest = pdfReader.pages[0].extract_text().split('\n')
		employer = pageOfInterest[0] #Seems to be the rule in this case.
		employeeName = ""
		payPeriodEnding = ""
		totalPretaxIncome = ""
		for index, line in enumerate(pageOfInterest):
			if employeeName == "" and "Name: " in line:
				words = line.split(' ')
				for word in words[1:]: #Cut out the first word as it will be "Name: "
					if word == "Employee" :
						#once we reach the end of the name, break.
						break
					employeeName += word + " "
				employeeName.strip() 
			elif totalPretaxIncome == "" and "3. TOTAL TAXABLE EARNINGS" in line:
				words = pageOfInterest[index+1].strip().split(" ")
				totalPretaxIncome = words[0]
			elif payPeriodEnding == "" and "Period End Date: " in line:
				words = line.split(' ')
				payPeriodEnding = words[-1]

		# Calculate the start of the pay period.
		ppStart = datetime.strptime(payPeriodEnding, "%d-%m-%Y") - timedelta(days=payPeriodLength)

		fullDict = {
			"name":fileName.split("/")[-1],
			"employeeName":employeeName,
			"employer":employer,
			"totalPretaxIncome":totalPretaxIncome,
			"payPeriodStart":ppStart.strftime("%d-%m-%Y"),
			"payPeriodEnding":payPeriodEnding,
			"data":psDict
		}
		#print(json.dumps(fullDict, indent=4))
		return fullDict

	#print("-------")
	
	

#print(json.dumps(ingestPDF("test.pdf"), indent=4))
