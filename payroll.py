from datetime import datetime, timedelta
import json
import holidays

"""
rosterDict = {
	"2023-10-31": "0700-1900",
    "2023-11-01": "0700-1600",
    "2023-11-02": "0700-1400",
    ...
}
"""

#DESCRIPTIONS
DESCRIPTORS_SHIFTS_PENS = { #These rates are (penalty rate + 1) because when first calculated, they INCLUDE the base hours as well.
	"1.2":"PENALTIES AT 20%",
	"1.25":"PENALTIES AT 25%",
	"1.5":"PENALTIES AT 50%",
	"1.75":"PENALTIES AT 75%",
	"PH2.5":"PUBLIC HOLIDAY 1.5" # This is a PENALTY too!
}
DESCRIPTORS_SHIFTS_ALL = DESCRIPTORS_SHIFTS_PENS.copy()
DESCRIPTORS_SHIFTS_ALL.update({
	"1":"BASE HOURS",
	"OT1.5":"OVERTIME @ 1.5",
	"OT2":"OVERTIME @ 2.0",
	"PH01":"PUBLIC HOLIDAY OBSERVED",
	"PH1":"BASE HOURS"
})

#OVERTIME
OVERTIME_RATES = {
	"80.0":1.5,
	"120.0":2
}
#PENALTIES (INCLUDING base hours, i.e. rates + 1)
#Legend: DOW:{after these hours, pay this rate}
PENALTY_RATES = {
	"Mon": {"0000":1.75, "0800":1, "1800":1.20},
	"Tue": {"0000":1.25, "0800":1, "1800":1.20},
	"Wed": {"0000":1.25, "0800":1, "1800":1.20},
	"Thu": {"0000":1.25, "0800":1, "1800":1.20},
	"Fri": {"0000":1.25, "0800":1, "1800":1.20},
	"Sat": {"0000":1.50},
	"Sun": {"0000":1.75}
}
# keys may ONLY be integers, as they are used as offset!!
# (PH are paid at 150% pens + base from midnight to 8am the following day)
PENALTY_RATES_PH_GENERIC = {
	"0": {"0000":2.5},
	"1": {"0000":2.5, "0800":1}
}
PENALTY_RATES_PH = {} #Created dynamically later.
PUBLIC_HOLIDAYS = {} #Created later by generatePublicHolidays()

WAGE_BASE_RATE = 42.3298
USUAL_HOURS = 8 #Used for PH observed calculation.
PH_TOTAL_RATE = 2.5 #This is used to calculate the cutoff for a 'futile' shift on a PH (i.e. one where working a small amount of hours at PH rate earns you less than simply not working and getting the observed base rate)
HOURS_BEFORE_OVERTIME = 80
#ON CALL (in $ not a multipler)
JMO_ON_CALL_HOURLY = 12.22


def generatePublicHolidays():
	PUBLIC_HOLIDAYS_TEMP = {}
	thisYear = datetime.now().strftime("%Y")
	au_holidays = holidays.AU(subdiv='WA',years=int(thisYear))
	for PH in au_holidays.items():
		PUBLIC_HOLIDAYS_TEMP.update({PH[0]:PH[1]})
	#For some reason Easter Sunday not included in this holidays library??
	PUBLIC_HOLIDAYS_TEMP.update({(au_holidays.get_named("Good Friday")[0]+timedelta(days=2)):"Easter Sunday"})
	#For some reason the Kings Birthday is wrong in this library
	PUBLIC_HOLIDAYS_TEMP.pop(au_holidays.get_named("King's Birthday")[0])
	PUBLIC_HOLIDAYS_TEMP.update({datetime.strptime("23-09-"+thisYear, "%d-%m-%Y").date():"King's Birthday"})
	#Sort the holidays by date because idk why they aren't sorted...
	theList = list(PUBLIC_HOLIDAYS_TEMP.keys())
	for x in sorted(theList):
		PUBLIC_HOLIDAYS.update({x:PUBLIC_HOLIDAYS_TEMP[x]})
	return PUBLIC_HOLIDAYS

generatePublicHolidays()


def createDateRangeDays(start, end):
	returnList = [start]
	x = 1
	while True:
		if end in returnList:
			break
		returnList.append(start + timedelta(days=x))
		x += 1
	return returnList

#hoursWorkedAlready (float) - the employee has worked this many hours already this fortnight.
#hoursAmount (float) - the employe now is working this many hours, and we need to know what portions of it will be allocated to overtime rates.
#returnValues (list) containing {"rate":rate, "hours":hours} objects
def getCorrectOTRates(hoursWorkedAlready, hoursAmount, debug):
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
			overhang = total - OTRateCheckpoint
			# If all hoursAmount fits in this OT-rate band, just dump it all as the single rate.
			if hoursAmount <= overhang:
				rate = OVERTIME_RATES[str(OTRateCheckpoint)]
				returnValues.append({"rate":rate, "hours":hoursAmount, "desc":DESCRIPTORS_SHIFTS_ALL["OT"+str(rate)]})
				return returnValues
			else:
				#This means there are more hours than will fit in this OT-rate band.
				#Deal with the maximum amount this band can.
				rate = OVERTIME_RATES[str(OTRateCheckpoint)]
				returnValues.append({"rate":rate, "hours":overhang, "desc":DESCRIPTORS_SHIFTS_ALL["OT"+str(rate)]})
				#And remove those "dealt with" hours from the hoursAmount to be done.
				hoursAmount -= overhang

	#Will return from here if no OT required to be paid out.
	if debug:
		print("no OT required with given values. alreadyWorked: " + str(hoursWorkedAlready) + ", hoursAmount: " + str(hoursAmount))
	return returnValues

def getCorrectPenRates(START_SHIFT_TIME, anchorBack):
	testRate = None
	if START_SHIFT_TIME.date() in PENALTY_RATES_PH:
		testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
		desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(testRate)]
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


# VERY IMPORTANT NOTE: this function ASSUMES the roster given contains shifts worked over a fortnight!.
# I.e. all shifts will be counted up and assumed to have occurred during a 14 day period.
def analyseRoster(rosterDict, debug=False):
	# -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE -------- SECTION ONE
	#rosterDict = {"2023-01-30": "0800-1900"}
	tempDict = {}
	returnDict = {}
	# tempDict = {date obj: [datetime obj SHIFT_START, datetime obj SHIFT_END]} (equivalent to the strings in rosterDict)

	baseHours = 0
	overtimeHours = 0
	dirtyAmountSum = 0 #Not used currently.

	# Generate the superior tempDict (datetime obj instead of strings)
	rangeLower = datetime.strptime("9999-12-30","%Y-%m-%d").date()
	rangeUpper = datetime.strptime("0001-01-01","%Y-%m-%d").date()
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
		if rangeLower > dtStart.date():
			rangeLower = dtStart.date()
		if rangeUpper < dtEnd.date():
			rangeUpper = dtEnd.date()
		tempDict.update({
			datetime.strptime(shift,"%Y-%m-%d"):[dtStart, dtEnd]
		})
		baseHours += (dtEnd - dtStart).seconds/3600 #difference in hours.
	if debug:
		print("rangeLOWER: " + datetime.strftime(rangeLower,"%d-%m-%Y"))
		print("rangeUPPER: " + datetime.strftime(rangeUpper,"%d-%m-%Y"))

	if baseHours > HOURS_BEFORE_OVERTIME:
		overtimeHours = baseHours - HOURS_BEFORE_OVERTIME
		baseHours = HOURS_BEFORE_OVERTIME
	if debug:
		print("BASE " + str(baseHours) + ", OT " + str(overtimeHours))
		print(tempDict)

	P_H_COPY = PUBLIC_HOLIDAYS.copy() #this will be modified to prevent double ups on PH that are already being worked.
	# Start by checking if you're already working PH

	daysWorking = createDateRangeDays(rangeLower, rangeUpper)
	for date in daysWorking:
		if date in PUBLIC_HOLIDAYS:
			if debug:
				print("------PH -------Already working")
			P_H_COPY.pop(date) #So it won't be counted when scanning through this dict next.
			# But still need to update the PH penalty rates dict as we know you'll be working. (see below where we do this again.)
			for offset in PENALTY_RATES_PH_GENERIC:
				PENALTY_RATES_PH.update({date+timedelta(days=int(offset)):PENALTY_RATES_PH_GENERIC[offset]})
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
			for offset in PENALTY_RATES_PH_GENERIC:
				PENALTY_RATES_PH.update({PH+timedelta(days=int(offset)):PENALTY_RATES_PH_GENERIC[offset]})

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

	runningHoursTotal = 0 #used exclusively to keep track of when OT must be enacted.
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
			if day in PUBLIC_HOLIDAYS:
				for hourMark in PENALTY_RATES_PH[day]: #uses a date as key instead of DoW like the other PENALTY RATES table.
					toAdd = datetime.strptime(hourMark, "%H%M")
					checkpoints.append(datetime.combine(day, toAdd.time()))
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
						if START_SHIFT_TIME.date() in PENALTY_RATES_PH: #This check of start_time is so you can access the until-8am-next-day part of PH rates.
							rate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
							desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
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
							if START_SHIFT_TIME.date() in PENALTY_RATES_PH:
								testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(testRate)]
							else:
								testRate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL[str(testRate)]
						except KeyError as e:
							pass # This will occur when the start time is not an actual penalty checkpoint.
							# If it does occur, the rate will have already been set by the loop the previous time (see the most outer else:)
						if not (testRate is None):
							rate = testRate

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
						if START_SHIFT_TIME.date() in PENALTY_RATES_PH: 
							rate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
							desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)] #Hopefully have pre-arranged these checkpoints such that rates are either 1.5 or 2
						else:
							rate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
							desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
					else:
						testRate = None
						try: #Try to see if the start time is also a valid penalty rate checkpoint.
							if START_SHIFT_TIME.date() in PENALTY_RATES_PH:
								testRate = PENALTY_RATES_PH[anchorBack.date()][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(testRate)]
							else:
								testRate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
								desc = DESCRIPTORS_SHIFTS_ALL[str(testRate)]
						except KeyError as e:
							pass # This will occur when the start time is not an actual penalty checkpoint.
							# If it does occur, the rate will have already been set by the loop the previous time (see the most outer else:)
						if not (testRate is None):
							rate = testRate
					pensList.append({"rate":rate, "hours":hrs, "desc":desc})
					# Prepare to move the anchor onwards sailor.
					anchorBack = anchorFront	
			else:
				#While trying to find START_SHIFT_TIME, make sure rate is updated with the most recent checkpoint.
				# This is because once you find the START_, will need the pens value behind the start to calculate correctly.
				if anchorFront.date() in PENALTY_RATES_PH:
					rate = PENALTY_RATES_PH[anchorFront.date()][anchorFront.strftime("%H%M")]
					desc = DESCRIPTORS_SHIFTS_ALL["PH"+str(rate)]
				else:
					rate = PENALTY_RATES[anchorFront.strftime("%a")][anchorFront.strftime("%H%M")]
					desc = DESCRIPTORS_SHIFTS_ALL[str(rate)]
		if debug:
			print({shift:pensList})

	# -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR -------- SECTION FOUR

		#ENSURE OT is factored in. (pens will be wrong if we breach the overtime hours limit and don't record the rate as the OT rate.)
		# If we have already breached the rate OR we will with the addition of this shift.
		shiftHrsDuration = (END_SHIFT_TIME - START_SHIFT_TIME).seconds/3600
		if runningHoursTotal >= HOURS_BEFORE_OVERTIME or (runningHoursTotal+shiftHrsDuration) > HOURS_BEFORE_OVERTIME:
			if debug:
				print('OVERTIME ACTIVATED')
			tempPensList = []
			for index, penaltyEntry in enumerate(pensList):
				# SORT OUT the 'remaining hours' portion of this rate, if applicable (i.e. a part will be at pre-OT rate, and a part at OT rate.)
				remainingHours = HOURS_BEFORE_OVERTIME - runningHoursTotal
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
					for entry in getCorrectOTRates(runningHoursTotal, (penaltyEntry["hours"]-remainingHours), debug):
						if entry["rate"] >= originalRate:	# Only add the OT version if it's rate is BETTER than the original. But preference recording hours at OT even if they are equivalent rates.
							tempPensList.append(entry)
						else:
							tempPensList.append({"rate":originalRate, "hours":penaltyEntry["hours"]-remainingHours, "desc":penaltyEntry["desc"]})
					runningHoursTotal += (penaltyEntry["hours"] - remainingHours)
					if debug:
						print("OTCALC | splitted | added: " +str(penaltyEntry["hours"]))
				else:
					for entry in getCorrectOTRates(runningHoursTotal, penaltyEntry["hours"], debug):
						if entry["rate"] >= penaltyEntry["rate"]:	# Only add the OT version if it's rate is BETTER than the original. But preference recording hours at OT even if they are equivalent rates.
							tempPensList.append(entry)
						else:
							# This only usually occurs if a sunday is worked and considered overtime - sunday rate is better (75% pens + base > 1.5)
							tempPensList.append(penaltyEntry)
					runningHoursTotal += penaltyEntry["hours"]
					if debug:
						print("OTCALC | no split required | added: " +str(penaltyEntry["hours"]))
			pensList = tempPensList
			if debug:
				print("----------------------\npensList:")
				print(pensList)
				print("----------------------")
		else:
			runningHoursTotal += shiftHrsDuration

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
				rateProper = (entry["rate"]-1)*WAGE_BASE_RATE
				dirtyAmountSum += rateProper*entry["hours"]
				pensListProper.append({
					"description":entry["desc"],
					"units":str(entry["hours"]),
					"rate":str(round(rateProper,4)),
					"amount":str(round(rateProper*entry["hours"], 2))
				})
			else:
				#Add as per usual
				rateProper = entry["rate"]*WAGE_BASE_RATE
				dirtyAmountSum += rateProper*entry["hours"]
				pensListProper.append({
					"description":entry["desc"],
					"units":str(entry["hours"]),
					"rate":str(round(rateProper,4)),
					"amount":str(round(rateProper*entry["hours"],2))
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



