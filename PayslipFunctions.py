import PyPDF2
import yaml
import sys

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
	"MEAL - DINNER MED PRACT"
]

def ingestPDF(fileName):
	#Payslip Dictionary (the end product of ingesting the payslip)
	psDict = {}
	with open(fileName, 'rb') as pdf:
		pdfReader = PyPDF2.PdfReader(pdf)
		pageOfInterest = pdfReader.pages[1].extract_text().split('\n')
		LINELIMITER = 0
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
			


	#print("-------")
	#print(yaml.dump(psDict, default_flow_style=False))
	return psDict

