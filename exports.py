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
def exportStudy(studyDict, stateVersion="WA"):
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

	filepath = "./export-" + datetime.now().strftime("%d-%m-%Y-%H%M") + ".xlsx"
	wb.save(filepath)

# exportStudy({
#     "13-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "14-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "15-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "4.0",
#             "rate": "42.3298",
#             "amount": "169.32"
#         }
#     ],
#     "16-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "17-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "18-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "14.5",
#             "rate": "42.3298",
#             "amount": "613.78"
#         },
#         {
#             "description": "PENALTIES AT 50%",
#             "units": "14.5",
#             "rate": "21.1649",
#             "amount": "306.89"
#         }
#     ],
#     "20-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "21-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "22-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "4.0",
#             "rate": "42.3298",
#             "amount": "169.32"
#         }
#     ],
#     "23-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "8.0",
#             "rate": "42.3298",
#             "amount": "338.64"
#         }
#     ],
#     "24-02-2023": [
#         {
#             "description": "BASE HOURS",
#             "units": "1.5",
#             "rate": "42.3298",
#             "amount": "63.49"
#         },
#         {
#             "description": "OVERTIME @ 1.5",
#             "units": "6.5",
#             "rate": "63.4947",
#             "amount": "412.72"
#         }
#     ]
# })