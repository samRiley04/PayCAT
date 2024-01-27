import PyPDF2
import openpyxl
from openpyxl import load_workbook
import yaml
from datetime import datetime
from datetime import time
from dateutil import parser
import json
import re

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
		# the 'or' part allows matching of 0800 as well as 800 (meaning 8am).
		s = re.search(r'(\d{4}|[1-9]\d{2}|000)\s*-\s*(\d{4}|[1-9]\d{2}|000)', string)
	except TypeError:
		pass
	if not s is None:
		times = s.group().replace(' ','').split("-")
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

#given openpyxl cell object containing a date check if it's "valid"
# Valid date entries have a shift entry below them (at least somewhere) and DONT have dates below them.
# SENSITIVITY MAY NEED TO BE TITRATED TO EFFECT in future. (titrate marginValue)
def dateValidTypeB(cell, sheet):
	counter = 0
	# After marginValue number of cells that dont contain valid strings, consider this date INVALID.
	marginValue = 4
	# Create a range and iterate (next #marginValue cells not including the date cell itself.)
	for rowDown in sheet[cell.column_letter+str(cell.row+1):cell.column_letter+str(cell.row+marginValue)]:
		for cellDown in rowDown:
			counter += 1
			print("date: " + str(cell.value) + " | checking: " + str(cellDown.value))
			if not (parseHours(cellDown.value) is None):
				# Got at least one valid string before the marginValue cutoff, so it's Valid.
				return True
			elif not (cellDown.value is None):
				# If you encounter any non-hours-like shit below, it's likely invalid
				return False
			elif counter >= marginValue:
				# Unclear if invalid (only saw empty cells)
				# Create a range and iterate
				if cell.column == 1:
					compareLeft = "<INVALID_DATE>"
				else:
					compareLeft = str(sheet.cell(row=cell.row, column=cell.column-1).value)
				compareRight = str(sheet.cell(row=cell.row, column=cell.column+1).value)
				print("R: ")
				print(compareRight)
				print("L: ")
				print(compareLeft)
				# If either of left or right are valid dates.
				if (parseDate(compareLeft) or parseDate(compareRight)):
					return True
				return False

# RETURN ERRORS
# ValueError - "employee name not found", "recognisable dates not found"
# 
def ingestRoster(fileName):
	debug = True
	findName = "Samuel Riley"
	rosterFormat = "B"
	startDate = datetime.strptime("2023-08-21", "%Y-%m-%d")
	endDate = datetime.strptime("2023-08-27", "%Y-%m-%d")
	outputDict = {}

	wb = load_workbook(fileName, data_only=True)
	if rosterFormat == "A":
		pass
	elif rosterFormat == "B":
		sheet = wb.active
		tempDates = {}
		# find DATE CELLS
		# AND check validity of DATES simultaneously
		for row in sheet.iter_rows():
			for cell in row:
				# If the cell isn't empty
				if not (cell.value is None):
					dateAttempt = parseDate(str(cell.value))
					#parseDate returns None if it doesn't match a date.
					if not (dateAttempt is None):
						# Then check if it's a valid bonafide date. (check down first, if that fails, laterally)
						if dateValidTypeB(cell, sheet):
							# Copy whole cell object so can access row/col easier.
							tempDates.update({
								str(dateAttempt):cell
							})
						elif debug:
							print("DISCARDING potential date: " + dateAttempt)
		if len(tempDates) == 0:
			#Found no recognisable dates in the roster
			raise ValueError("No recognisable dates found in the roster.")
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
			raise ValueError("Employee name not found in roster. Is it spelled correctly?")
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
		#Now all the roster is ingested, trim the dict using the start/end dates.
		copy = outputDict.copy()
		for entry in copy:
			e = datetime.strptime(entry, "%Y-%m-%d")
			if not (e >= startDate and e <= endDate):
				outputDict.pop(entry)

		return outputDict
	elif rosterFormat == "C":
		sheet = wb.active
		tempDates = {}
		# find and store DATE ROWS
		for col in sheet.iter_cols():
			for cell in col:
				# If the cell isn't empty
				if not (cell.value is None):
					attempt = parseDate(str(cell.value))
					#parseDate returns None if it doesn't match a date.
					if not attempt is None:
						tempDates.update({
				    		str(cell.row):str(attempt)
				   		})
		if len(tempDates) == 0:
			#Found no recognisable dates in the roster
			raise ValueError("No recognisable dates found in the roster.")	
		# find NAME COLS
		tempNameCols = []
		for row in sheet.iter_rows():
			for cell in row:
				if cell.value == findName and not (cell.value in tempNameCols):
					tempNameCols.append(str(cell.column_letter))
		if len(tempNameCols) == 0:
			# Did not find a name.
			raise ValueError("Employee name not found in roster. Is it spelled correctly?")
		# create outputDict
		for col in tempNameCols:
			for row in tempDates:
				hrs = parseHours(sheet[str(col)+str(row)].value)
				if not hrs is None:
					# Only update the dict if hours worked is a value
					outputDict.update({tempDates[row]:hrs})

		#print(json.dumps(outputDict, indent=4))

		#Now all the roster is ingested, trim the dict using the start/end dates.
		copy = outputDict.copy()
		for entry in copy:
			e = datetime.strptime(entry, "%Y-%m-%d")
			if not (e >= startDate and e <= endDate):
				outputDict.pop(entry)

		return outputDict

	else:
		#the fuck?
		return 0








print(json.dumps(ingestRoster("TESTING/Nsurg.xlsx"), indent=4))

def ingestPDF(fileName):
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

		fullDict = {
			"employeeName":employeeName,
			"employer":employer,
			"totalPretaxIncome":totalPretaxIncome,
			"payPeriodEnding":payPeriodEnding,
			"data":psDict
		}

		return fullDict

	#print("-------")
	#print(yaml.dump(psDict, default_flow_style=False))
	

#ingestPDF("test2.pdf")
