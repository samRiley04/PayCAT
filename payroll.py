from datetime import datetime, timedelta
import json

"""
rosterDict = {
	"2023-10-31": "0700-1900",
    "2023-11-01": "0700-1600",
    "2023-11-02": "0700-1400",
    ...
}
"""

#DESCRIPTIONS
DESCRIPTORS_SHIFTS_PENS = {
	"1.2":"PENALTIES AT 20%",
	"1.25":"PENALTIES AT 25%",
	"1.5":"PENALTIES AT 50%",
	"1.75":"PENALTIES AT 75%"
}
DESCRIPTORS_SHIFTS_ALL = DESCRIPTORS_SHIFTS_PENS.copy()
DESCRIPTORS_SHIFTS_ALL.update({
	"1":"BASE HOURS",
	"OT1.5":"OVERTIME @ 1.5",
	"OT2":"OVERTIME @ 2.0",
	"PH1.5":"PUBLIC HOLIDAY 1.5"
})

#OVERTIME
HOURS_BEFORE_OVERTIME = 80
OVERTIME_RATES = {
	"80.0":1.5,
	"120.0":2
}
#ON CALL (in $ not a multipler)
JMO_ON_CALL_HOURLY = 12.22

#PENALTIES (on top of base hours)
#DOW {after these hours, pay this pen rate}
PENALTY_RATES = {
	"Mon": {"0000":1.75, "0800":1, "1800":1.25},
	"Tue": {"0000":1.20, "0800":1, "1800":1.25},
	"Wed": {"0000":1.20, "0800":1, "1800":1.25},
	"Thu": {"0000":1.20, "0800":1, "1800":1.25},
	"Fri": {"0000":1.20, "0800":1, "1800":1.25},
	"Sat": {"0000":1.50},
	"Sun": {"0000":1.75}
}

#PUBLIC HOLIDAYS 2024
#Should be generated dynamically - TODO
PUBLIC_HOLIDAYS = {
	datetime.strptime("01-01-2023", "%d-%m-%Y").date():"New Years Day",
	datetime.strptime("26-01-2023", "%d-%m-%Y").date():"Australia Day",
	datetime.strptime("25-04-2023", "%d-%m-%Y").date():"Anzac Day",
	datetime.strptime("29-03-2023", "%d-%m-%Y").date():"Good Friday"
}

WAGE_BASE_RATE = 42.3298

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
	# Include public holidays that must be observed
	for shift in tempDict:
		if shift.date() in PUBLIC_HOLIDAYS:
			print("CUM--------CUM--------CUM--------CUM--------")




	if baseHours > HOURS_BEFORE_OVERTIME:
		overtimeHours = baseHours - HOURS_BEFORE_OVERTIME
		baseHours = HOURS_BEFORE_OVERTIME
	if debug:
		print("BASE " + str(baseHours) + ", OT " + str(overtimeHours))
		print(tempDict)


	P_H_COPY = PUBLIC_HOLIDAYS.copy()
	# Start by checking if you're already working PH
	for shift in tempDict.copy():
		if shift.date() in PUBLIC_HOLIDAYS:
			if debug:
				print("------PH -------Already working")
			P_H_COPY.pop(shift.date()) #So it won't be counted when scanning through this dict next.
	print(P_H_COPY)
	for PH in P_H_COPY:
		if PH <= rangeUpper and PH >= rangeLower:
			if debug:
				print("------PH -------Added placeholder")
				d1 = datetime.combine(PH, datetime.strptime("0000", "%H%M").time())
				tempDict.update({
					d1:[d1,d1]
				})

	runningHoursTotal = 0 #used exclusively to keep track of when OT must be enacted.
	for shift in tempDict:
		# then can move on to CALCULATING PENALTIES (ignore possibility of overtime/public holidays and not contributing to runningHoursTotal)
		START_SHIFT_TIME = tempDict[shift][0]
		END_SHIFT_TIME = tempDict[shift][1]
		daysToCheck = [START_SHIFT_TIME.date()] #often nightshifts stretch the shift over more than one day
		checkpoints = [] #used to calculate penalties

		# If the shift stretches over more than one day (e.g. nightshift)
		if not START_SHIFT_TIME.date() == END_SHIFT_TIME.date():
			# Assumption: a shift cant last more than 24 hours (I hope this stays true forever...)
			daysToCheck.append(END_SHIFT_TIME.date())
		if debug:
			print("daysToCheck: " + str(daysToCheck))

		# Create CHECKPOINTS from the dictionary containing penalty rate cutoffs.
		for day in daysToCheck:
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
		#Now calculate hours intervals using a worm-crawling approach.
		anchorBack = None
		pensList = []
		rate = None
		for indx, anchorFront in enumerate(checkpoints):
			if anchorFront == START_SHIFT_TIME:
				anchorBack = START_SHIFT_TIME
			# Once first anchored, start collecting hours.
			elif not (anchorBack is None):
				hrs = None
				if anchorFront == END_SHIFT_TIME:
					# Has the anchor reached the end shift time? Need to look ahead to get the correct penalty rates for these hours then.
					#creates timedelta obj
					hrs = float((END_SHIFT_TIME - anchorBack).seconds/3600)
					# This will override the rate no matter what (if there are overtime hours)
					if not (anchorBack == START_SHIFT_TIME):
						rate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
					# ^this is equivalent to PENALTY_RATES["Mon"]["1800"]
					pensList.append({"rate":rate, "hours":hrs, "desc":DESCRIPTORS_SHIFTS_ALL[str(rate)]})
					#We need not iterate further, as we have reached endshifttime.
					break
				else:
					# So the anchor must be on a checkpoint then.
					#creates timedelta obj
					hrs = float((anchorFront - anchorBack).seconds/3600)
					# This will override the rate no matter what (if there are overtime hours)
					# Use the penalty_rates dict to look up the correct rate for this interval.
					# The correct pen is determined by backanchor (and if it's not a true checkpoint, whatever is behind back anchor.)
					# If the back anchor is on start shift, the rate we want is already set through the enclosing if-else statement. Thus, look for not this case.
					if not (anchorBack == START_SHIFT_TIME):	
						rate = PENALTY_RATES[anchorBack.strftime("%a")][anchorBack.strftime("%H%M")]
					pensList.append({"rate":rate, "hours":hrs, "desc":DESCRIPTORS_SHIFTS_ALL[str(rate)]})
					# Prepare to move the anchor onwards sailor.
					anchorBack = anchorFront	
			else:
				#While trying to find START_SHIFT_TIME, make sure rate is updated with the most recent checkpoint.
				# This is because once you find the START_, will need the pens value behind the start to calculate correctly.
				rate = PENALTY_RATES[checkpoints[indx].strftime("%a")][anchorFront.strftime("%H%M")]
		if debug:
			print({shift:pensList})

		#ENSURE OT is factored in. (pens will be wrong if we breach the overtime hours limit and don't record the rate as the OT rate.)
		# If we have already breached the rate OR we will with the addition of this shift.
		shiftHrsDuration = (END_SHIFT_TIME - START_SHIFT_TIME).seconds/3600
		if runningHoursTotal >= HOURS_BEFORE_OVERTIME or (runningHoursTotal+shiftHrsDuration) >= HOURS_BEFORE_OVERTIME:
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
						runningHoursTotal += penaltyEntry["hours"]
						continue
					# Only reach this point if the current penaltyEntry has to be split up
					# I.e. if there are remaining hours, and the current entry has more than that amount to ingest/parse.
					originalRate = penaltyEntry["rate"]
					# Delete the original - we will replace it.
					tempPensList.append({"rate":originalRate, "hours":remainingHours, "desc":penaltyEntry["desc"]})
					runningHoursTotal += remainingHours
					# Still have to add (penaltyEntry["hours"] - remainingHours) hours at overtime rate.
					for entry in getCorrectOTRates(runningHoursTotal, (penaltyEntry["hours"]-remainingHours), debug):
						if entry["rate"] > originalRate:	# Only add the OT version if it's rate is BETTER than the original.
							tempPensList.append(entry)
						else:
							tempPensList.append({"rate":originalRate, "hours":penaltyEntry["hours"]-remainingHours, "desc":penaltyEntry["desc"]})
					runningHoursTotal += (penaltyEntry["hours"] - remainingHours)
					if debug:
						print("OTCALC | splitted | added: " +str(penaltyEntry["hours"]))
				else:
					for entry in getCorrectOTRates(runningHoursTotal, penaltyEntry["hours"], debug):
						if entry["rate"] > penaltyEntry["rate"]:	# Only add the OT version if it's rate is BETTER than the original.
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

		# TIDY up and collate the penalty list for that day.
		# Get a list of unique rates in the pensList
		pensList = tidyAndCollatePensList(pensList)
		# Multiply out to now take record BASE HOURS correctly. (previously, counting them alongside pens hours would be illogical and very challenging, but they are recorded seperately in the payslip)
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
	
	print("INGESTED ROSTER. OUTPUT:")
	print(json.dumps(returnDict, indent=2))
	return returnDict





test = {
	"2023-04-08": "0830-1630",
    "2023-04-09": "0830-1630",
    "2023-04-10": "0830-1230",
    "2023-04-11": "0830-1630",
    "2023-04-12": "0830-1630",
    "2023-04-13": "0830-2300",
    "2023-04-25": "0830-1630",
    "2023-04-26": "0830-1630",
    "2023-04-27": "0830-1230",
    "2023-04-28": "0830-1630",
    "2023-04-29": "0830-1630"
}
# --------- UP TO: public holidays observed placeholder bug

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
analyseRoster(test, debug=True)



