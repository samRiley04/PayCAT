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
	# This regular expression makes me aroused
	# the 'or' part allows matching of 0800 as well as 800 meaning 8am.
	s = re.search(r'(\d{4}|[1-9]\d{2}|000)\s*-\s*(\d{4}|[1-9]\d{2}|000)', string)
	if not s is None:
		times = s.group().replace(' ','').split("-")
		for t in times:
			# Regex has ensured this is safe to do - if time has no leading zero, add it. (required for datetime)
			if len(t) == 3:
				t = "0"+t
		dif = datetime.strptime(times[1], "%H%M") - datetime.strptime(times[0], "%H%M")
		return float((dif.seconds/60)/60)
	else:
		return None


def ingestRoster(fileName):
	findName = "RILEY"
	rosterFormat = "C"
	startDate = "2022-11-07"
	endDate = "2022-11-13"
	outputDict = {}

	wb = load_workbook(fileName)

	if rosterFormat == "A":
		pass
	elif rosterFormat == "B":
		pass
	elif rosterFormat == "C":
		for sheet in wb:
			tempDates = {}
			# find DATE ROWS
			for row in sheet.iter_cols():
				for cell in row:
					# If the cell isn't empty
					if not (cell.value is None):
						try:
						    parser.parse(str(cell.value))
						    # Add the cell to the dict of dates.
						    tempDates.update({
						    	str(cell.row):str(cell.value)
						    })
						except ValueError as e:
							#Doesn't identify cell as a date.
							pass
					else:
						pass		
					#print(type(cell.value))
			print(json.dumps(tempDates , indent=4))
			# find NAME COLS
			tempNameCols = []
			for row in sheet.iter_rows():
				for cell in row:
					if cell.value == findName:
						tempNameCols.append(str(cell.column_letter))
			# create outputDict
			for col in tempNameCols:
				for row in tempDates:
					outputDict.update({tempDates[row]:parseHours(sheet[str(col)+str(row)].value)})

			print(outputDict)			

			#Only do one sheet for now	
			break
	else:
		#the fuck?
		return 0








ingestRoster("TESTING/test.xlsx")

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
