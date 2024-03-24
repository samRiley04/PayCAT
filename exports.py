import openpyxl
from openpyxl import load_workbook
from datetime import datetime, timedelta
from datetime import time
from dateutil import parser
import json
import re
import custom_exceptions as ex

import payroll as pr

EXPORT_DURATION = 28 #days
def exportStudy(studyDict, stateVersion="WA", saveFilePath=None):
	wb = openpyxl.Workbook()
	sheet = wb.active

	print("EXPORTING ", studyDict)

	descList = []
	if stateVersion == "NT":
		descList = list(pr.DESCRIPTORS_SHIFTS_ALLOTHERS_NT.values())
		descList.extend(list(pr.DESCRIPTORS_SHIFTS_PENS_NT.values()))
	elif stateVersion == "WA":
		descList = list(pr.DESCRIPTORS_SHIFTS_ALLOTHERS_WA.values())
		descList.extend(list(pr.DESCRIPTORS_SHIFTS_PENS_WA.values()))	
	descList = list(set(descList))
	descList.sort()


	descDict = {} #Stores the row that this description is located in.
	start = 2
	for desc in descList:
		sheet["A"+str(start)] = desc
		descDict.update({desc:start}) #filling descDict
		start += 1

	start = 3
	dateDict = {}
	startDate = datetime.strptime(list(studyDict.keys())[0], "%d-%m-%Y")
	for offset in range(0,EXPORT_DURATION-1):
		sheet.cell(row=1,column=start).value = startDate.strftime("%d-%m-%Y")
		dateDict.update({startDate.strftime("%d-%m-%Y"):start})
		startDate += timedelta(days=1)
		start += 1

	for date, hoursList in studyDict.items():
		for hoursType in hoursList:
			sheet.cell(row=descDict[hoursType["description"]], column=dateDict[date]).value = float(hoursType["units"])

	if not saveFilePath:
		print("USING DEFAULT FILE NAME")
		saveFilePath = "./export-" + datetime.now().strftime("%Y-%m-%d-%H%M") + ".xlsx"
	# if not re.search(r'^\./', saveFilePath):
	# 	raise ValueError("File Path not in correct format")
	wb.save(saveFilePath) #No real way of knowing if this was successful
	return True

