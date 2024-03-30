from datetime import datetime, timedelta
import json
import holidays
import locale
locale.setlocale(locale.LC_ALL, '')

import urllib.request
import math
from decimal import *
getcontext().prec = 26
getcontext().rounding = ROUND_HALF_DOWN
DEC_EIGHTPLACES = Decimal(10) ** -8
DEC_FOURPLACES = Decimal(10) ** -4
DEC_TWOPLACES = Decimal(10) ** -2
DEC_ONEPLACE = Decimal(10) ** -1

import re

def multi(a, b, sf=DEC_EIGHTPLACES):
	return (a*b).quantize(sf, rounding=ROUND_HALF_UP)

import custom_exceptions as ex


# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# START HARDCODED SETTINGS
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


#DESCRIPTIONS
DESCRIPTORS_SHIFTS_PENS = {}
DESCRIPTORS_SHIFTS_PENS_WA = { #These rates are (penalty rate + 1) because when first calculated, they INCLUDE the base hours as well.
	"1.2":"PENALTIES AT 20%",
	"1.25":"PENALTIES AT 25%",
	"1.5":"PENALTIES AT 50%",
	"1.75":"PENALTIES AT 75%",
	"PH2.5":"PUBLIC HOLIDAY 1.5" # This is a PENALTY too!
}
DESCRIPTORS_SHIFTS_PENS_NT = { #These rates are (penalty rate + 1) because when first calculated, they INCLUDE the base hours as well.
	"1.15":"PENALTIES AT 15%",
	"1.225":"PENALTIES AT 22.5%",
	"1.5":"PENALTIES AT 50%",
	"2":"PENALTIES AT 100%",
	"PH2.5":"PUBLIC HOLIDAY 1.5" # This is a PENALTY too!
}
DESCRIPTORS_SHIFTS_ALL = {}
DESCRIPTORS_SHIFTS_ALLOTHERS_WA = {
	"1":"BASE HOURS",
	"OT1.5":"OVERTIME @ 1.5",
	"OT2":"OVERTIME @ 2.0",
	"PHO1":"PUBLIC HOLIDAY (OBSERVED)",
	"PH1":"BASE HOURS",
	"PDA":"PROFESSIONAL DEVT ALLOW"
}
DESCRIPTORS_SHIFTS_ALLOTHERS_NT = {
	"1":"BASE HOURS",
	"OT1.5":"OVERTIME 1.5x",
	"OT2":"OVERTIME 2.0x",
	"PHO1":"PUBLIC HOLIDAY OBSERVED",
	"PH1":"BASE HOURS",
	"0":"UNPAID MEAL BREAK"
}

DESCRIPTORS_OTHER_WA = [
	"SMART SALARY SP FIXED",
	"MEAL - DINNER MED PRACT",
	"SICK LVE NO CERT FULLPAY",
	"OVERTIME @1.75" #this one is a bit sus.. does that exist?
]
DESCRIPTORS_OTHER_NT = []

#OVERTIME
OVERTIME_RATES = {}
# In a TWO WEEK Period.
OVERTIME_RATES_WA = {
	"80.0":{
		"Mon": 1.5,
		"Tue": 1.5,
		"Wed": 1.5,
		"Thu": 1.5,
		"Fri": 1.5,
		"Sat": 1.5,
		"Sun": 1.5
	},
	"120.0":{
		"Mon": 2,
		"Tue": 2,
		"Wed": 2,
		"Thu": 2,
		"Fri": 2,
		"Sat": 2,
		"Sun": 2
	}
}
# In a FOUR WEEK PERIOD !!! i.e. >38hours/week averaged over 4 weeks.
OVERTIME_RATES_NT = {
	"152.0":{
		"Mon": 1.5,
		"Tue": 1.5,
		"Wed": 1.5,
		"Thu": 1.5,
		"Fri": 1.5,
		"Sat": 2,
		"Sun": 2
	}
}

#PENALTIES (INCLUDING base hours, i.e. rates + 1)
#Legend: DOW:{after these hours, pay this rate}
PENALTY_RATES = {}
PENALTY_RATES_WA = {
	"Mon": {"0000":1.75, "0800":1, "1800":1.20},
	"Tue": {"0000":1.25, "0800":1, "1800":1.20},
	"Wed": {"0000":1.25, "0800":1, "1800":1.20},
	"Thu": {"0000":1.25, "0800":1, "1800":1.20},
	"Fri": {"0000":1.25, "0800":1, "1800":1.20},
	"Sat": {"0000":1.50},
	"Sun": {"0000":1.75}
}
PENALTY_RATES_NT = {
	"Mon": {"0000":1.225, "0600":1, "1800":1.15},
	"Tue": {"0000":1.225, "0600":1, "1800":1.15},
	"Wed": {"0000":1.225, "0600":1, "1800":1.15},
	"Thu": {"0000":1.225, "0600":1, "1800":1.15},
	"Fri": {"0000":1.225, "0600":1, "1800":1.15},
	"Sat": {"0000":1.50},
	"Sun": {"0000":2}
}

def CHECK_PENRATES():
	required = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
	for x in required:
		if not x in PENALTY_RATES:
			raise ex.Insurmountable("The penalty rates dictionary (PENALTY_RATES) does not contain an entry for every day of the week. This is required for normal functioning.")
		for key, value in PENALTY_RATES[x].items():
			if not re.search(r'^\d{4}$', key):
				raise ex.Insurmountable("The penalty rates dictionary (PENALTY_RATES) entry for '{dow}' contains an invalid hours checkpoint entry - '{key}'.".format(dow=x, key=key))
			if not (isinstance(value, float) or isinstance(value, int)):
				raise ex.Insurmountable("The penalty rates dictionary (PENALTY_RATES) entry for '{dow}' contains a value entry that is not float or integer - '{val}'.".format(dow=x, val=value))

# keys may ONLY be integers, as they are used as offset!!
PENALTY_RATES_PH_GENERIC = {}
PENALTY_RATES_PH_GENERIC_WA = {
	"0": {"0000":2.5},
	"1": {"0000":2.5, "0800":1}
}
PENALTY_RATES_PH_GENERIC_NT = {
	"0": {"0000":2.5},
	"1": {"0000":1.225, "0600":1, "1800":1.15} #I.e. back to a normal day.
}

def CHECK_PENRATES_PH_GENERIC():
	if not "0" in PENALTY_RATES_PH_GENERIC:
		raise ex.Insurmountable("The generic public holiday rates dictionary (PENALTY_RATES_PH_GENERIC) does NOT contain a key equal to '0'. This is one of the only requirements. See documentation 'payroll-functions.md'")
	for x in PENALTY_RATES_PH_GENERIC:
		if not re.search(r'^\d$', x): #If not a single digit
			raise ex.Insurmountable("The generic public holiday rates dictionary (PENALTY_RATES_PH_GENERIC) contains a key that is not an integer.")

PENALTY_RATES_PH = {} #Created dynamically later.
PUBLIC_HOLIDAYS = {} #Created later by generatePublicHolidays()

WAGE_BASE_RATE = None
USUAL_HOURS = None #Used for PH observed calculation.
PH_TOTAL_RATE = None #This is used to calculate the cutoff for a 'futile' shift on a PH (i.e. one where working a small amount of hours at PH rate earns you less than simply not working and getting the observed base rate)
HOURS_BEFORE_OVERTIME = None #filled below

# -----------------------------------------------------------------------------------------------------------------------------------------------------------
# END HARDCODED SETTINGS
# -----------------------------------------------------------------------------------------------------------------------------------------------------------

# This includes TRUE public holidays, as well as SUBSTITUTE public holidays (I.e. where a public holiday occurs on a weekend and is observed on the next Monday)
def generatePublicHolidays(yearsList, stateVersion, debug=True):
	PUBLIC_HOLIDAYS_TEMP = {}
	au_holidays = holidays.AU(subdiv=stateVersion,years=yearsList)
	for PH in au_holidays.items():
		PUBLIC_HOLIDAYS_TEMP.update({PH[0]:PH[1]})
	#For some reason Easter Sunday not included in this holidays library??
	for event in au_holidays.get_named("Good Friday"):
		PUBLIC_HOLIDAYS_TEMP.update({(event+timedelta(days=2)):"Easter Sunday"})
	if stateVersion == "WA":
		#For some reason this library gets the Kings Birthday wrong for 2024
		for birthday in au_holidays.get_named("King's Birthday"):
			if birthday.year == "2024":
				PUBLIC_HOLIDAYS_TEMP.pop(birthday)
				PUBLIC_HOLIDAYS_TEMP.update({datetime.strptime("23-09-2024", "%d-%m-%Y"):"King's Birthday"})
				break
	elif stateVersion == "NT":
		pass #TODO Christmas even and NY eve.
	# Holidays lib does get observed holiday days correct, but unfortunately the AMA agreement doesn't consider all of them as paid public holidays
	# So some must be removed. Note - Christmas is not removed, see documentation 'payroll-functions.md'
	dontRemoveFromWknds = ["Christmas Day", "Easter Saturday", "Easter Sunday"]
	for date, name in PUBLIC_HOLIDAYS_TEMP.copy().items():
		if date.strftime("%a") in ["Sat", "Sun"] and name not in dontRemoveFromWknds: #Double negative - equates to if name in removefromweekends
			PUBLIC_HOLIDAYS_TEMP.pop(date)
		# This relies on the (observed) public holiday versions already being in the library.
	# Sort them.
	theList = list(PUBLIC_HOLIDAYS_TEMP.keys())
	for x in sorted(theList):
		PUBLIC_HOLIDAYS.update({x:PUBLIC_HOLIDAYS_TEMP[x]})
	if debug:
		print(f"JUST GENERATED THESE {stateVersion} PUBLIC HOLIDAYS: {PUBLIC_HOLIDAYS}")
	return PUBLIC_HOLIDAYS

# DIRECTLY modifies PENALTY_RATES_PH.
def makePenratePHEntry(date, debug=True):
	for offset in PENALTY_RATES_PH_GENERIC:
		if offset == "0":
				# Day 0 - Rate NOT blended.
				PENALTY_RATES_PH.update({date+timedelta(days=int(offset)):PENALTY_RATES_PH_GENERIC[offset]})
				if debug:
					print(f"ADDED: {date+timedelta(days=int(offset))} with rates: {PENALTY_RATES_PH_GENERIC[offset]}")
		else:
			# Day 1 (AKA day after PH) - Rate MUST be blended with the normal rates seen on that day of the week (so as to include the after 6pm pen, or so that the rest of the day is at 1.75 or 1.5 for weekends.)
			blendedRates = blendRatesDicts(PENALTY_RATES_PH_GENERIC[offset], PENALTY_RATES[(date+timedelta(days=int(offset))).strftime("%a")])
			if debug:
				print(f"ADDED: {date+timedelta(days=int(offset))} with rates: {blendedRates}")
			PENALTY_RATES_PH.update({date+timedelta(days=int(offset)):blendedRates})

def createDateRangeDays(start, end):
	returnList = [start]
	x = 1
	while True:
		if end in returnList:
			break
		returnList.append(start + timedelta(days=x))
		x += 1
	return returnList

def createDateRangeYears(start,end):
	returnList = [start.year]
	x = start.year+1
	while True:
		if end.year in returnList:
			break
		returnList.append(x)
		x += 1
	return returnList

#Returns a single rates dictionary, combining the penalty rate values, preferring the highest value.
# Used to apply a day-after-public holiday rate to a weekday/weekend day (for the remaining hours after 8am). 
# E.g. {"0000":1.25} and {"0000":1.5} returns {"0000":1.5}
# E.g. {"0000":2.5, "0800":1} and {"0000":1.25, "0800":1, "1800":1.20} returns {"0000":2.5, "0800":1, "1800":1.20} ---DAY AFTER PUBLIC HOLIDAY IS WEEKDAY E.G
# E.g. {"0000":2.5, "0800":1} and {"0000":1.75} returns {"0000":2.5, "0800":1.75} ---DAY-AFTER-PH IS SUNDAY E.G
def blendRatesDicts(first, second, debug=True):
	# Make a master set of checkpoints
	t = list(first.keys())
	t.extend(list(second.keys()))
	blendCheckpoints = list(set(t)) #uniqueify
	blendCheckpoints.sort()
	listOfThem = [first, second]
	# Make sure they have matching checkpoint times but preserve their rates-data (ensures rates can be compared truly accurately in the next step)
	for index, aRatesDict in enumerate(listOfThem.copy()):
		currentRate = None
		for checkpoint in blendCheckpoints:
			if not (checkpoint in aRatesDict):
				if currentRate is None:
					continue # See documentation - if the rate is not defined prior to a missing checkpoint, it doesn't need to be added. Step two will favour the other dictionary anyway (which is the desired functionality)
				listOfThem[index].update({checkpoint:currentRate})
			currentRate = aRatesDict[checkpoint]
	# Now create toReturn using both dicts, prioritising the higher rates values
	toReturn = {}
	for checkpoint in blendCheckpoints:
		for thisRatesDict in listOfThem:
			if checkpoint in thisRatesDict:
				# Eligible to potentially be added to the return dict..
				if (checkpoint in toReturn) and (toReturn[checkpoint] < thisRatesDict[checkpoint]):
					toReturn.update({checkpoint:thisRatesDict[checkpoint]}) #If this checkpoint is already in the return dict, ONLY update it if the rates value is BETTER
				elif not checkpoint in toReturn:
					toReturn.update({checkpoint:thisRatesDict[checkpoint]}) #This is just for readability - could be one big OR statement.
	if debug:
		print("--> BLENDED Rates Dicts created: ", toReturn)
		print("--> USING: " + str(first) + " and "+ str(second))
	return toReturn


#hoursWorkedAlready (float) - the employee has worked this many hours already this fortnight.
#hoursAmount (float) - the employe now is working this many hours, and we need to know what portions of it will be allocated to overtime rates.
#returnValues (list) containing {"rate":rate, "hours":hours} objects
#DoWToday - what day of the week this OT is being checked for (determines rate)
def getCorrectOTRates(hoursWorkedAlready, hoursAmount, DoWToday, debug):
	returnValues = []
	# Create a more useable version of the overtime rates dict (hour-checkpoints now in float form)
	toIterate = list(OVERTIME_RATES.keys())
	for i, x in enumerate(toIterate.copy()):
		toIterate[i] = float(x)
	toIterate.sort(reverse=True) #Largest numbers first for reasons that you will see ahead.

	# Work through each checkpoint, wasting away hoursAmount once those hours have been added to returnValues.
	for OTRateCheckpoint in toIterate:
		total = hoursWorkedAlready + hoursAmount
		# Will there be ANY hours in this OT rate band (as definited by checkpoint as the lower limit)
		if total > OTRateCheckpoint:
			overhang = total - Decimal(OTRateCheckpoint)
			# If all hoursAmount fits in this OT-rate band, just dump it all as the single rate.
			if hoursAmount <= overhang:
				rate = OVERTIME_RATES[str(OTRateCheckpoint)][DoWToday]
				returnValues.append({"rate":(Decimal(rate).quantize(DEC_EIGHTPLACES, rounding=ROUND_HALF_UP)).quantize(DEC_FOURPLACES, rounding=ROUND_HALF_UP), "hours":hoursAmount.quantize(DEC_TWOPLACES), "desc":DESCRIPTORS_SHIFTS_ALL["OT"+str(rate)]})
				return returnValues
			else:
				#This means there are more hours than will fit in this OT-rate band.
				#Deal with the maximum amount this band can.
				rate = OVERTIME_RATES[str(OTRateCheckpoint)][DoWToday]
				returnValues.append({"rate":(Decimal(rate).quantize(DEC_EIGHTPLACES, rounding=ROUND_HALF_UP)).quantize(DEC_FOURPLACES, rounding=ROUND_HALF_UP), "hours":overhang.quantize(DEC_TWOPLACES), "desc":DESCRIPTORS_SHIFTS_ALL["OT"+str(rate)]})
				#And remove those "dealt with" hours from the hoursAmount to be done.
				hoursAmount -= overhang

	#Will return from here if no OT required to be paid out.
	if debug:
		print("Adding this overtime packet! ", returnValues)
	return returnValues

def getCorrectPenRates(START_SHIFT_TIME, anchorBack):
	testRate = None
	if START_SHIFT_TIME.date() in PENALTY_RATES_PH:
		testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
		try:
			desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
		except (KeyError):
			desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
	else:
		testRate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
		desc = DESCRIPTORS_SHIFTS_ALL[str(testRate)]
	return testRate

def tidyAndCollatePensList(pensList):
	uniq = []
	for entry in pensList:
		uniq.append(entry["desc"])
	uniq = set(uniq)
	# Collate all duplicate rates in pens list.
	tempPensList = []
	for desc in uniq:
		# Sum each rate now.
		sumHours = 0
		rate = None
		for entry in pensList:
			if entry["desc"] == desc:
				sumHours+= entry["hours"]
				rate = entry["rate"]
		tempPensList.append({"rate":rate, "hours":sumHours, "desc":desc})
	tempPensList.sort(key=lambda x: x["rate"])
	return tempPensList

def expandForBaseHours(pensList):
	#Find every entry containing a penalty rate description, and create a duplicate with the BASEHOURS rate.
	for entry in pensList:
		if entry["desc"] in DESCRIPTORS_SHIFTS_PENS.values():
			pensList.append({"rate":1, "hours":entry["hours"], "desc":DESCRIPTORS_SHIFTS_ALL["1"]})
	# Multiple entries for base hours created per penalty, thus have to tidy again.
	return tidyAndCollatePensList(pensList)

def setGlobalDicts(stateVersion):
	global DESCRIPTORS_SHIFTS_PENS
	global DESCRIPTORS_SHIFTS_ALL
	global OVERTIME_RATES
	global PENALTY_RATES
	global PENALTY_RATES_PH_GENERIC

	if stateVersion == "WA":
		global DESCRIPTORS_SHIFTS_PENS_WA
		DESCRIPTORS_SHIFTS_PENS = DESCRIPTORS_SHIFTS_PENS_WA

		DESCRIPTORS_SHIFTS_ALL = DESCRIPTORS_SHIFTS_PENS.copy()

		global DESCRIPTORS_SHIFTS_ALLOTHERS_WA
		DESCRIPTORS_SHIFTS_ALL.update(DESCRIPTORS_SHIFTS_ALLOTHERS_WA)
		
		global OVERTIME_RATES_WA
		OVERTIME_RATES = OVERTIME_RATES_WA

		global PENALTY_RATES_WA
		PENALTY_RATES = PENALTY_RATES_WA

		global PENALTY_RATES_PH_GENERIC_WA
		PENALTY_RATES_PH_GENERIC = PENALTY_RATES_PH_GENERIC_WA
	elif stateVersion == "NT":
		global DESCRIPTORS_SHIFTS_PENS_NT
		DESCRIPTORS_SHIFTS_PENS = DESCRIPTORS_SHIFTS_PENS_NT

		DESCRIPTORS_SHIFTS_ALL = DESCRIPTORS_SHIFTS_PENS.copy()

		global DESCRIPTORS_SHIFTS_ALLOTHERS_NT
		DESCRIPTORS_SHIFTS_ALL.update(DESCRIPTORS_SHIFTS_ALLOTHERS_NT)
		
		global OVERTIME_RATES_NT
		OVERTIME_RATES = OVERTIME_RATES_NT

		global PENALTY_RATES_NT
		PENALTY_RATES = PENALTY_RATES_NT

		global PENALTY_RATES_PH_GENERIC_NT
		PENALTY_RATES_PH_GENERIC = PENALTY_RATES_PH_GENERIC_NT
	else:
		raise ex.Insurmountable("Invalid state version: ", stateVersion)

# VERY IMPORTANT NOTE: this function ASSUMES the roster given contains shifts worked over a fortnight!.
# I.e. all shifts will be counted up and assumed to have occurred during a 14 day period.
def analyseRoster(rosterDict, wageBaseRate, usualHours, stateVersion, debug=True):
	setGlobalDicts(stateVersion)
	print(stateVersion)
	CHECK_PENRATES_PH_GENERIC()
	CHECK_PENRATES()
	PH_TOTAL_RATE = PENALTY_RATES_PH_GENERIC["0"]["0000"]
	HOURS_BEFORE_OVERTIME = float(list(OVERTIME_RATES.keys())[0])

	# debug=True
	if rosterDict == {}:
		raise ValueError("Found no recognisable dates in the roster for this given range.")
	WAGE_BASE_RATE = wageBaseRate
	USUAL_HOURS = usualHours
	# -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE
	#rosterDict = {"2023-01-30": "0800-1900"}
	tempDict = {}
	returnDict = {}
	# tempDict = {date obj: [datetime obj SHIFT_START, datetime obj SHIFT_END]} (equivalent to the strings in rosterDict)

	baseHours = 0
	overtimeHours = 0
	dirtyAmountSum = Decimal(0) #Not used currently.

	# Generate the superior tempDict (datetime obj instead of strings)
	rangeLower = None
	rangeUpper = None
	for shift in rosterDict:
		shiftStart = rosterDict[shift].split('-')[0]
		shiftEnd = rosterDict[shift].split('-')[1]
		dtStart = datetime.strptime(shift+" "+shiftStart, "%Y-%m-%d %H%M")
		dtEnd = datetime.strptime(shift+" "+shiftEnd, "%Y-%m-%d %H%M")
		#Accounting for nightshifts (e.g. where "2200-0800" means 10pm to 8am the following day)
		if dtStart > dtEnd:
			dtEnd += timedelta(days=1)
			if debug:
				print("Making a night shift work proper.")

		#Used to detect public holidays.
		if (rangeLower is None) or (rangeLower > dtStart.date()):
			rangeLower = dtStart.date()
		if (rangeUpper is None) or (rangeUpper < dtEnd.date()):
			rangeUpper = dtEnd.date()
		tempDict.update({
			datetime.strptime(shift,"%Y-%m-%d"):[dtStart, dtEnd]
		})
		baseHours += (dtEnd - dtStart).seconds/3600 #difference in hours.
	if debug:
		print("rangeLOWER: " + datetime.strftime(rangeLower,"%d-%m-%Y"))
		print("rangeUPPER: " + datetime.strftime(rangeUpper,"%d-%m-%Y"))

	# Using the start and end times of our roster, create all potential public holiday dates we could encounter.
	PUBLIC_HOLIDAYS = generatePublicHolidays(createDateRangeYears(rangeLower, rangeUpper), stateVersion, debug)

	if baseHours > HOURS_BEFORE_OVERTIME:
		overtimeHours = baseHours - HOURS_BEFORE_OVERTIME
		baseHours = HOURS_BEFORE_OVERTIME
	if debug:
		print("BASE " + str(baseHours) + ", OT " + str(overtimeHours))
		print("---- tempDict !!! ----")
		print(tempDict)

	P_H_COPY = PUBLIC_HOLIDAYS.copy() #this will be modified to prevent double ups on PH that are already being worked.
	# Start by checking if you're already working PH

	daysWorking = list(tempDict.keys())
	if debug:
		print("DAYS WORKING: ")
		print(daysWorking)

	needsPHPenrateMade = [] # List of dates that require individual penalty rates made for them (as they are public holidays)
	# ASSUMPTION - PENALTY_RATES_PH_GENERIC contains AT MOST two entries - 0 and 1
	for date in daysWorking:
		date = date.date()
		# POP DATES and MAKE A PEN_RATE_PH ENTRY
		if date in PUBLIC_HOLIDAYS:
			if debug:
				print("------PH -------Already working")
			P_H_COPY.pop(date) #So it won't be counted when scanning through this dict next.
			# But still need to update the PH penalty rates dict as we know you'll be working. (see below where we do this again.)
			# makePenratePHEntry(date)
			needsPHPenrateMade.append(date)
		# MAKE A PEN_RATE_PH ENTRY only.
		elif (date - timedelta(days=1)) in PUBLIC_HOLIDAYS: #If working the day _AFTER_ a PH, need to have that PEN_RATE_PH entry in the dict, but don't want it to be removed from P_H_COPY otherwise it won't be recognised as an observed PH in the next step
			if debug:
				print("------PH -------Working Day after, making PEN_RATE entry only")
			# makePenratePHEntry(date-timedelta(days=1))
			needsPHPenrateMade.append(date-timedelta(days=1))
	if debug:
		print("PUBLIC HOLIDAYS MODIFIED:")
		print(P_H_COPY)
	for PH in P_H_COPY:
		if PH <= rangeUpper and PH >= rangeLower:
			if debug:
				print("------PH -------Adding placeholder of zero hours")
			# You're not working this day, but it still must be added as PH observed, so include an empty shift on that day so it will be counted. (see PH observed/worked logic later on)
			d1 = datetime.combine(PH, datetime.strptime("0000", "%H%M").time())
			# d2 = datetime.combine(PH, datetime.strptime("0800", "%H%M").time())
			# d3 = d2 + timedelta(hours=USUAL_HOURS)
			tempDict.update({
				d1:[d1,d1]
			})
			# Because we know we will be calculating rates on this day, generate an entry for PENALTY_RATES_PH
			# Remembering that the keys in this dict are the offsets from the PH day, with units being days.
			# This will overwrite any second-days that may have already been placed (e.g. in the case of christmas day and boxing day) but this IS CORRECT.
			# makePenratePHEntry(PH)
			needsPHPenrateMade.append(PH)

	needsPHPenrateMade = list(set(needsPHPenrateMade)) #uniquify
	needsPHPenrateMade.sort()
	print(f"To make penrates for: {needsPHPenrateMade}")
	for givenDate in needsPHPenrateMade: # Recording them and then making penrates all at once in chronological order ensures the "day-after" penalty rates are recorded correctly and not overwriting actual public holidays.
		makePenratePHEntry(givenDate)

	if debug:
		print("PENALTY RATES PUBLIC HOLIDAY")
		print(PENALTY_RATES_PH)

	# Sort tempDict by it's keys.
	replace = {}
	tds = list(tempDict.keys())
	for key in sorted(tds):
		replace.update({key:tempDict[key]})
	tempDict = replace

	# -------- SECTION TWO -------- SECTION TWO -------- SECTION TWO -------- SECTION TWO -------- SECTION TWO -------- SECTION TWO -------- SECTION TWO	

	runningHoursTotal = Decimal(0) #used exclusively to keep track of when OT must be enacted.
	#NOW take each shift, and create a list of penalties, how many hours they apply to, and the description of that data.
	#Call that list pensList (its declared later on.)
	for shift in tempDict:
		# CALCULATING PENALTIES (ignore possibility of overtime/public holidays and not contributing to runningHoursTotal. These are done afterwards.)
		START_SHIFT_TIME = tempDict[shift][0]
		END_SHIFT_TIME = tempDict[shift][1]
		daysToCheck = [START_SHIFT_TIME.date()] #often nightshifts stretch the shift over more than one day, may need to add more than one day.
		checkpoints = [] #used to calculate penalties.

		# If the shift stretches over more than one day (e.g. nightshift)
		if not START_SHIFT_TIME.date() == END_SHIFT_TIME.date():
			# Assumption: a shift cant last more than 24 hours (I hope this stays true forever...)
			daysToCheck.append(END_SHIFT_TIME.date())
		if debug:
			print("daysToCheck: " + str(daysToCheck))

		# Create CHECKPOINTS from the dictionary containing penalty rate cutoffs.
		for day in daysToCheck:
			# If the day is a public holiday, insert checkpoints from the PH reference dict instead of the default DoW reference dict.
			if day in PENALTY_RATES_PH:
				for hourMark in PENALTY_RATES_PH[day]: #uses a date as key instead of DoW like the other PENALTY RATES table.
					toAdd = datetime.strptime(hourMark, "%H%M")
					checkpoints.append(datetime.combine(day, toAdd.time()))
					datetime.combine(day, toAdd.time())
			else:
				for hourMark in PENALTY_RATES[day.strftime("%a")]:
					toAdd = datetime.strptime(hourMark, "%H%M")
					# Take the base date and add on the datetime equivalent of hourMark.
					checkpoints.append(datetime.combine(day, toAdd.time()))

		#Throw the shift times in the mix
		if not (START_SHIFT_TIME in checkpoints):
			checkpoints.append(START_SHIFT_TIME)
		if not (END_SHIFT_TIME in checkpoints):
			checkpoints.append(END_SHIFT_TIME)
		#and then sort them into order.
		checkpoints.sort()
		if debug:
			print("CECHKPOINTS")
			for x in checkpoints:
				#print(x.strftime("%dth - %H%M"))
				print(x)

	# -------- SECTION THREE -------- SECTION THREE -------- SECTION THREE -------- SECTION THREE -------- SECTION THREE  -------- SECTION THREE -------- SECTION THREE
	

		#Now calculate hours intervals using a worm-crawling approach.
		anchorBack = None
		pensList = []
		rate = None
		desc = None
		for indx, anchorFront in enumerate(checkpoints):
			if anchorFront == START_SHIFT_TIME:
				anchorBack = START_SHIFT_TIME
				#HACKY WORKAROUND - if the shift is zero hours long, and the day is a public holiday, this is a PH OBSERVED shift! Because that's how I programmed it.
				#This check could go anywhere in this for loop as long as it is a standalone if, but I placed it in here so this check isn't done a million times unnecessarily.
				if START_SHIFT_TIME == END_SHIFT_TIME and anchorFront.date() in PUBLIC_HOLIDAYS:
					rate = 1
					desc = DESCRIPTORS_SHIFTS_ALL["PHO1"]
					hrs = USUAL_HOURS
					pensList.append({"rate":rate, "hours":hrs, "desc":desc})
			# Once first anchored, start collecting hours.
			elif not (anchorBack is None):
				hrs = None
				if anchorFront == END_SHIFT_TIME:
					# Has the anchor reached the end shift time? Need to look ahead to get the correct penalty rates for these hours then.
					#creates timedelta obj
					hrs = float((END_SHIFT_TIME - anchorBack).seconds/3600)
					# This will override the rate no matter what (if there are overtime hours)
					if not (anchorBack == START_SHIFT_TIME): #If the back anchor is on the shift_start time, we use the rate from what is already set last time (see the else clause in the most outside if/elif/else statement)
						if anchorBack.date() in PENALTY_RATES_PH: #This check of start_time is so you can access the until-8am-next-day part of PH rates.
							rate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
							try:
								desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
							except (KeyError):
								desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
						else: #rate must be reset as back anchor is ending on a checkpoint.
							rate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
							desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
					else:
						# CRUCIAL - check for a 'futile shift'.
						if (anchorBack.date() in PUBLIC_HOLIDAYS) and (hrs < (USUAL_HOURS/PH_TOTAL_RATE)): 
							# Convert this futile shift into a PH Observed shift.
							hrs = USUAL_HOURS
							rate = 1
							desc = DESCRIPTORS_SHIFTS_ALL["PHO1"]
							# This 'if' is only placed once as PH shifts will always have START_TIME and END_TIME sequential, as theres' only one checkpoint at 0000. (assumption B)
						testRate = None
						try: #Try to see if the start time is also a valid penalty rate checkpoint.
							if anchorBack.date() in PENALTY_RATES_PH:
								testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
								try:
									desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
								except (KeyError):
									desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
							else:
								testRate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL[str(testRate)]
						except KeyError as e:
							pass # This will occur when the start time is not an actual penalty checkpoint.
							# If it does occur, the rate will have already been set by the loop the previous time (see the most outer else:)
						if not (testRate is None):
							rate = testRate
							desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]

					pensList.append({"rate":rate, "hours":hrs, "desc":desc})
					#We need not iterate further, as we have reached endshifttime.
					break
				else:
					# So the anchor must be on a checkpoint then (or starttime).
					#creates timedelta obj
					hrs = float((anchorFront - anchorBack).seconds/3600)
					# This will override the rate no matter what (if there are overtime hours)
					# Use the penalty_rates dict to look up the correct rate for this interval.
					# The correct pen is determined by backanchor (and if it's not a true checkpoint, whatever is behind back anchor.)
					# If the back anchor is on start shift, the rate we want is already set through the enclosing if-else statement. Thus, look for not this case.
					if not (anchorBack == START_SHIFT_TIME):	
						if anchorBack.date() in PENALTY_RATES_PH: 
							rate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
							try:
								desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
							except (KeyError):
								desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
						else:
							rate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
							desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
					else:
						testRate = None
						try: #Try to see if the start time is also a valid penalty rate checkpoint.
							if anchorBack.date() in PENALTY_RATES_PH:
								testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
								try:
									desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
								except (KeyError):
									desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
							else:
								testRate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL[str(testRate)]
						except KeyError as e:
							pass # This will occur when the start time is not an actual penalty checkpoint.
							# If it does occur, the rate will have already been set by the loop the previous time (see the most outer else:)
						if not (testRate is None):
							rate = testRate
							desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
					pensList.append({"rate":rate, "hours":hrs, "desc":desc})
					# Prepare to move the anchor onwards sailor.
					anchorBack = anchorFront	
			else:
				#While trying to find START_SHIFT_TIME, make sure rate is updated with the most recent checkpoint.
				# This is because once you find the START_, will need the pens value behind the start to calculate correctly.
				if anchorFront.date() in PENALTY_RATES_PH:
					rate = PENALTY_RATES_PH[anchorFront.date()][anchorFront.strftime("%H%M")]
					try:
						desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
					except (KeyError):
						desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
				else:
					rate = PENALTY_RATES[anchorFront.strftime("%a")][anchorFront.strftime("%H%M")]
					desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
		if debug:
			print({shift:pensList})

		# NT ONLY - INCORPORATE UNPAID MEAL BREAKS
		# Subtract 30 minutes from ANY shift and enter it as a meal break. This does not contribute to overtime.
		# Allocates the meal break during the CHEAPEST pay rate during your shift.
		pensListMealbreak = [] #Stored here so they aren't counted in OT calculations.
		if stateVersion == "NT":
			allocateInCheapestRate = True
			print("----------------------- meal break BIT")
			print(json.dumps(pensList, indent=2))
			mealBreakShift = (0, pensList[0])
			for index, entry in enumerate(pensList):
				if allocateInCheapestRate: #Just in case I need to change it's functionality to be the opposite
					if entry["rate"] < mealBreakShift[1]["rate"] and entry["hours"] >= 0.5:
						mealBreakShift = (index, entry)
				else: 
					if entry["rate"] > mealBreakShift[1]["rate"] and entry["hours"] >= 0.5:
						mealBreakShift = (index, entry)

			#Validate - if there are no shifts of any duration more than 30 mins, don't take a meal break.
			if mealBreakShift[1]["hours"] >= 0.5:
				mealBreakShift[1]["hours"] -= 0.5
				pensList[mealBreakShift[0]] = mealBreakShift[1]
				pensListMealbreak.append({"rate":0,
						"hours":0.5,
						"desc":DESCRIPTORS_SHIFTS_ALL["0"]})


			print("---------------------- meal break END")
			print(json.dumps(pensList, indent=2))


	# -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR

		#ENSURE OT is factored in. (pens will be wrong if we breach the overtime hours limit and don't record the rate as the OT rate.)
		# If we have already breached the rate OR we will with the addition of this shift.
		shiftHrsDuration = Decimal((END_SHIFT_TIME - START_SHIFT_TIME).seconds/3600)
		if stateVersion == "NT" and len(pensListMealbreak) != 0: #NT ONLY - if we took a meal break, remove that time.
			shiftHrsDuration -= Decimal(0.5)

		if runningHoursTotal >= Decimal(HOURS_BEFORE_OVERTIME) or (runningHoursTotal+shiftHrsDuration) > HOURS_BEFORE_OVERTIME:
			if debug:
				print('OVERTIME ACTIVATED')
			tempPensList = []
			for index, penaltyEntry in enumerate(pensList):
				# SORT OUT the 'remaining hours' portion of this rate, if applicable (i.e. a part will be at pre-OT rate, and a part at OT rate.)
				remainingHours = Decimal(HOURS_BEFORE_OVERTIME) - runningHoursTotal
				if remainingHours > 0:
					if penaltyEntry["hours"] <= remainingHours:
						# No more OT logic to be done as we know this penalty entry isnt large enough to breach the OT threshhold, so just move on.
						# We haven't fiddled with the pensList but these 'skipped' hours have still been parsed/counted, so must add them to the running total.
						# They pass through to the tempPensList unperturbed.
						runningHoursTotal += penaltyEntry["hours"]
						tempPensList.append({"rate":penaltyEntry["rate"], "hours":penaltyEntry["hours"], "desc":penaltyEntry["desc"]})
						continue
					# Only reach this point if the current penaltyEntry has to be split up
					# I.e. if there are remaining hours, and the current entry has more than that amount to ingest/parse.
					originalRate = penaltyEntry["rate"]
					# Delete the original - we will replace it.
					tempPensList.append({"rate":originalRate, "hours":remainingHours, "desc":penaltyEntry["desc"]})
					runningHoursTotal += remainingHours
					# Still have to add (penaltyEntry["hours"] - remainingHours) hours at overtime rate.
					for entry in getCorrectOTRates(runningHoursTotal.quantize(DEC_TWOPLACES), (Decimal(penaltyEntry["hours"])-remainingHours), START_SHIFT_TIME.strftime("%a"), debug):
						if entry["rate"] >= originalRate:	# Only add the OT version if it's rate is BETTER than the original. But preference recording hours at OT even if they are equivalent rates.
							tempPensList.append(entry)
						else:
							tempPensList.append({"rate":originalRate, "hours":Decimal(penaltyEntry["hours"])-remainingHours, "desc":penaltyEntry["desc"]})
					runningHoursTotal += (Decimal(penaltyEntry["hours"]) - remainingHours)
					if debug:
						print("OTCALC | splitted | added: " +str(penaltyEntry["hours"]))
				else:
					for entry in getCorrectOTRates(runningHoursTotal, Decimal(penaltyEntry["hours"]), START_SHIFT_TIME.strftime("%a"), debug):
						if entry["rate"] >= penaltyEntry["rate"]:	# Only add the OT version if it's rate is BETTER than the original. But preference recording hours at OT even if they are equivalent rates.
							tempPensList.append(entry)
						else:
							# This only usually occurs if a sunday is worked and considered overtime - sunday rate is better (75% pens + base > 1.5)
							tempPensList.append(penaltyEntry)
					runningHoursTotal += Decimal(penaltyEntry["hours"])
					if debug:
						print("OTCALC | no split required | added: " +str(penaltyEntry["hours"]))
			pensList = tempPensList
			if debug:
				print("----------------------\npensList:")
				print(pensList)
				print("----------------------")
		else:
			runningHoursTotal += shiftHrsDuration
		runningHoursTotal = runningHoursTotal.quantize(DEC_TWOPLACES)

		# NT ONLY - Add in MEAL BREAKS now OT is calculated.
		if stateVersion == "NT":
			pensList.extend(pensListMealbreak)

		if debug:
			print("runningHoursTotal = " + str(runningHoursTotal))

	# -------- SECTION FIVE -------- SECTION FIVE -------- SECTION FIVE -------- SECTION FIVE -------- SECTION FIVE -------- SECTION FIVE -------- SECTION FIVE

		# TIDY up and collate the penalty list for that day.
		# Condense penslist to only one entry per rate, collating hours along the way.
		pensList = tidyAndCollatePensList(pensList)
		# Multiply out to now to record BASE HOURS correctly. (previously, counting them alongside pens hours would be illogical and very challenging, but they ARE recorded seperately in the payslip)
		pensList = expandForBaseHours(pensList)

		# Finally, iterate through the list and create the output format.
		pensListProper = []

		for entry in pensList:
			# Make sure to record penalties correctly by separating base hours and penalty rate values
			if entry["desc"] in DESCRIPTORS_SHIFTS_PENS.values():
				#Just have to modify the rate before continuing.
				rateProper = multi(Decimal(entry["rate"]-1), Decimal(WAGE_BASE_RATE)).quantize(DEC_FOURPLACES, rounding=ROUND_HALF_UP) #weird but only way to get 5's to round down. Trust me.
				thisAmount = (Decimal(rateProper)*Decimal(entry["hours"])).quantize(DEC_TWOPLACES)
				dirtyAmountSum += thisAmount
				pensListProper.append({
					"description":entry["desc"],
					"units":str(entry["hours"]),
					"rate":str(rateProper),
					"amount":locale.currency(thisAmount, symbol=False)
				})
			else:
				#Add as per usual
				rateProper = multi(Decimal(entry["rate"]), Decimal(WAGE_BASE_RATE)).quantize(DEC_FOURPLACES, rounding=ROUND_HALF_UP) #See same term above.
				thisAmount = (Decimal(rateProper)*Decimal(entry["hours"])).quantize(DEC_TWOPLACES)
				dirtyAmountSum += thisAmount
				pensListProper.append({
					"description":entry["desc"],
					"units":str(entry["hours"]),
					"rate":str(rateProper),
					"amount":locale.currency(thisAmount, symbol=False)	
				})
		returnDict.update({shift.strftime("%d-%m-%Y"):pensListProper})
	if debug:
		print("INGESTED ROSTER. OUTPUT:")
		print(json.dumps(returnDict, indent=2))
	return returnDict





test = {
    "2024-12-19": "1800-0800"
}
"""
test = {
    "2023-01-30": "0830-1630",
    "2023-01-31": "0830-1630",
    "2023-02-01": "0830-1230",
    "2023-02-02": "0830-1630",
    "2023-02-03": "0830-1630",
    "2023-02-04": "0830-1130",
    "2023-02-07": "2245-0845",
    "2023-02-08": "2245-0845",
    "2023-02-09": "2245-0845",
    "2023-02-10": "2245-0845",
    "2023-02-11": "2245-0845"
}"""

#analyseRoster(test, debug=True)



