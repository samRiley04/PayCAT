import flask
from flask import Flask, redirect, url_for, render_template, flash, request, session, send_from_directory, current_app
from flask_restful import Resource, Api, reqparse, inputs
from multiprocessing import Process, Queue, freeze_support
from datetime import datetime, timedelta

import logging
import webbrowser
import requests
import shelve
import sys
import os
import json

#My files.
import PayslipFunctions as pFx
import payroll
import utilities as ut
import exports as exp

# Initialise
#To ensure this works packaged.
base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    #app = Flask("PayCAT", template_folder=template_folder)
    app = Flask(__name__,
        static_folder=os.path.join(base_dir, 'static'),
        template_folder=os.path.join(base_dir, 'templates'))
else:
    app = Flask("PayCAT")


logging.basicConfig(filename='server.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S%p')
api = Api(app)
#SHELF
SHELF_NAME = "PayCAT-shelf"
SHELF_NAME_SETTINGS = SHELF_NAME+"-settings"
with shelve.open(SHELF_NAME, writeback=True) as shlf:
	if not "_NEXT_ID" in shlf:
		shlf["_NEXT_ID"] = 1

with shelve.open(SHELF_NAME_SETTINGS, writeback=True) as shlf:
	if not "WAGE_BASE_RATE" in shlf:
		shlf["WAGE_BASE_RATE"] = None
	if not "USUAL_HOURS" in shlf:
		shlf["USUAL_HOURS"] = None
	if not "EMPLOYEE_NAME" in shlf:
		shlf["EMPLOYEE_NAME"] = None
	if not "WHICH_AUSSTATE_VERSION" in shlf:
		shlf["WHICH_AUSSTATE_VERSION"] = None
#?Do YAML config.

def isConfigDone():
	with shelve.open(SHELF_NAME_SETTINGS) as shlf:
		if (shlf["WAGE_BASE_RATE"] is None) or (shlf["USUAL_HOURS"] is None):
			return False
	return True

@app.route("/")
def home():
	return render_template("index.html")

@app.route("/help")
def help():
	return render_template("help.html")

# ------–––– API ------––––

class studiesDataList(Resource):
	def get(self):
		returnDict = {}
		# Essentially jsonify the entire shelf for transmitting.
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			for key in shlf:
				if not key == "_NEXT_ID":
					returnDict.update({key:shlf[key]})

		return {
			"data":returnDict,
			"message":"Success"
		}, 200


	# Get given a valid local filename, and then generate+store a psDict using that filename
	# Return the psDict just created (would just be calling GET anyway.)
	def post(self):
		debug = True
		# SAFETYCHECK
		if not isConfigDone():
			return {
				"data":None,
				"message":"Settings not yet configured."
			}, 503
		parser = reqparse.RequestParser()
		parser.add_argument("filePath")
		parser.add_argument("mode", required=True)
		# Optional
		parser.add_argument("rosterType")
		parser.add_argument("employeeName")
		parser.add_argument("startDate")
		parser.add_argument("endDate")
		parser.add_argument("filePath2")
		parser.add_argument("rosterType2")
		parser.add_argument("employeeName2")
		parser.add_argument("startDate2")
		parser.add_argument("endDate2")	
		parser.add_argument("exportID")
		parsed_args = parser.parse_args()
		print(json.dumps(parsed_args,indent=4))

		with shelve.open(SHELF_NAME_SETTINGS, writeback=True) as shlf:
			stateVersion = shlf["WHICH_AUSSTATE_VERSION"]

		# CREATE VIEW MODE ---
		if parsed_args["mode"] == "view":
			try:
				if parsed_args["filePath"].endswith(".pdf"):
					if stateVersion == "WA":
						shelfEntry = pFx.ingestPDF(parsed_args["filePath"]) #ingestPDF is a legacy payslip ingestion algorithm that I haven't changed yet
						shelfEntry["totalPretaxIncome"] = ut.deepSumAmounts(shelfEntry["data"])
					elif stateVersion == "NT":
						shelfEntry = pFx.ingestPayslip(parsed_args["filePath"], "NT", debug)
				elif parsed_args["filePath"].endswith(".xlsx"):
					with shelve.open(SHELF_NAME_SETTINGS) as shlf:
						baseRate = shlf["WAGE_BASE_RATE"]
						usualHours = shlf["USUAL_HOURS"]
					dataDict = payroll.analyseRoster(pFx.ingestRoster(parsed_args["filePath"], parsed_args["employeeName"], parsed_args["rosterType"], datetime.strptime(parsed_args["startDate"], "%d-%m-%Y"), datetime.strptime(parsed_args["endDate"], "%d-%m-%Y"), stateVersion), baseRate, usualHours, stateVersion)
					shelfEntry = {
						"name":parsed_args["filePath"].split("/")[-1],
						"employeeName": parsed_args["employeeName"],
						"employer": "Unknown",
						"totalPretaxIncome": ut.deepSumAmounts(dataDict),
						"payPeriodStart": parsed_args["startDate"],
						"payPeriodEnding": parsed_args["endDate"],
						"data": dataDict
					}
				else:
					return {
						"data": None,
						"message": "Incompatibile file type for file \'"+parsed_args["filePath"]+"\'"
					}, 415
				#Shelf save.
				with shelve.open(SHELF_NAME, writeback=True) as shlf:
					#Add candidate to shelf using the next unique ID
					newlyMadeID = str(shlf["_NEXT_ID"])
					shlf['_NEXT_ID'] += 1
					shlf[newlyMadeID] = {"view":shelfEntry}
					return {
						"data":{newlyMadeID: shlf[newlyMadeID]},
						"message":"Success"
					}, 201
			except (FileNotFoundError):
				return {
					"data": None,
					"message":"File not found."
				}, 404
			except(ValueError) as e:
				print(str(e))
				return {
					"data": None,
					"message": "Error: " + str(e)
				}, 404
		# CREATE COMPARE MODE ---
		elif parsed_args["mode"] == "compare":
			#Do some compare shit.
			shelfEntry = []
			# Dictionary-ify this data because for some reason ajax cannot manage to send it in this format.
			toIterate = [{"filePath":parsed_args["filePath"],
						"rosterType":parsed_args["rosterType"],
						"employeeName":parsed_args["employeeName"],
						"startDate":parsed_args["startDate"],
						"endDate":parsed_args["endDate"]
						}, {"filePath":parsed_args["filePath2"],
						"rosterType":parsed_args["rosterType2"],
						"employeeName":parsed_args["employeeName2"],
						"startDate":parsed_args["startDate2"],
						"endDate":parsed_args["endDate2"]
						}]
			for obj in toIterate:
				try:
					if obj["filePath"].endswith(".pdf"):
						if stateVersion == "WA":
							shelfEntry.append(pFx.ingestPDF(obj["filePath"])) #'dressed up' inside the function
							print("SHELF ENTRY", shelfEntry)
						elif stateVersion == "NT":
							shelfEntry.append(pFx.ingestPayslip(obj["filePath"], "NT", debug)) #'dressed up' inside the function
					elif obj["filePath"].endswith(".xlsx"):
						# Get the current settings
						with shelve.open(SHELF_NAME_SETTINGS) as shlf:
							baseRate = shlf["WAGE_BASE_RATE"]
							usualHours = shlf["USUAL_HOURS"]
						dataDict = payroll.analyseRoster(pFx.ingestRoster(obj["filePath"], obj["employeeName"], obj["rosterType"], datetime.strptime(obj["startDate"], "%d-%m-%Y"), datetime.strptime(obj["endDate"], "%d-%m-%Y")), baseRate, usualHours, stateVersion)
						shelfEntry.append({
							"name":obj["filePath"].split('/')[-1],
							"employeeName": obj["employeeName"],
							"employer": "Unknown",
							"totalPretaxIncome": ut.deepSumAmounts(dataDict),
							"payPeriodStart": obj["startDate"],
							"payPeriodEnding": obj["endDate"],
							"data": dataDict
						})
					else:
						return {
							"data": None,
							"message": "Incompatibile file type for file \'"+obj["filePath"]+"\'"
						}, 415
				except(FileNotFoundError) as e:
					return {
						"data": None,
						"message": "File not found - \'"+e+"\'"
					}, 404
				except(ValueError) as e:
					print(str(e))
					return {
						"data": None,
						"message": "Error: " + str(e)
					}, 404
			# Entry now constructed to standard, lets identify the discrepancies.
			discrepancies, globalDiscrepancies = ut.findDiscrepancies(shelfEntry, stateVersion)

			with shelve.open(SHELF_NAME, writeback=True) as shlf:
				newlyMadeID = str(shlf["_NEXT_ID"])
				shlf['_NEXT_ID'] += 1
				shlf[newlyMadeID] = {
					"compare":shelfEntry,
					"discrepancies": discrepancies,
					"globalDiscrepancies": globalDiscrepancies
				}
				return {
					"data":{newlyMadeID: shlf[newlyMadeID]},
					"message":"Success"
				}, 201
		elif parsed_args["mode"] == "export":
			with shelve.open(SHELF_NAME, writeback=True) as shlf:
				studyInQuestion = shlf[parsed_args["exportID"]]
				exportDict = None
				if "view" in studyInQuestion:
					exportDict = studyInQuestion["view"]["data"]
				elif "compare" in studyInQuestion:
					exportDict = studyInQuestion["compare"][0]["data"]
				defaultName = "export-{dateStr}.xlsx".format(dateStr=datetime.now().strftime("%Y-%m-%d-%H%M"))
				saveFilePath = "./{defaultName}".format(defaultName=defaultName)
				if __name__ == "__main__":
					q = Queue()
					p = Process(target=ut.fileSaver, args=(q,defaultName))
					p.start()
					saveFilePath = q.get()
					p.join()
				print("SAVE FILE PATH: ", saveFilePath)
				if not saveFilePath:
					print("No file name selected, cancelling.")
					return {
						"data":None,
						"message":"File save select cancelled."
					}, 408 #REQUEST TIMEOUT
				expResult = exp.exportStudy(exportDict, stateVersion, saveFilePath)
				if expResult:
					return {
						"data":None,
						"message":"File saved successfully."
					}, 200
				return {
						"data":None,
						"message":"File saving error."
					}, 400
		else:
			#Unknown mode.
			return {
				"data":None,
				"message":"Unknown mode supplied."
			}, 404


api.add_resource(studiesDataList, "/api/studydata")

class studyData(Resource):
	def get(self, studyID):

		### TEMPORARY 
		# disco, globDisco = ut.findDiscrepancies(testingLIST)
		# return {
		# 	"data": {"compare":testingLIST, "discrepancies":disco, "globalDiscrepancies":globDisco},
		# 	"message":"ASDaSD"
		# }, 200


		"""# Validate.
		if not pdfNameShort[-4:] == ".pdf":
			return {
				"data":None,
				"message":"Incorrect file type - pdfs only!"
			}, 415
			"""
		toReturn = {}
		# Retrieve that entry from the shelf if it exists.
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			try:
				toReturn = shlf[studyID]
			except (KeyError):
				return {
					"data":None,
					"message":"File not found."
				}, 404
		return {
			"data":toReturn,
			"message":"Success"
		}, 200

	def delete(self, studyID):
		# SAFETYCHECK
		if not isConfigDone():
			return {
				"data":None,
				"message":"Settings not yet configured."
			}, 503

		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			if studyID in shlf:
				shlf.pop(studyID)
				return {
					"data":None,
					"message":"Success"
				}, 204
			else:
				return {
					"data":None,
					"message":"Could not find file by that name."
				}, 404

api.add_resource(studyData, "/api/studydata/<string:studyID>")

class filePath(Resource):
	#Kinda counter intuitive - but GET the path because the application creates the file selector popup and gives the info back to the requester.
	def get(self):
		pickedPath = None
		if __name__ == "__main__":
			q = Queue()
			p = Process(target=ut.filePicker, args=(q,))
			p.start()
			pickedPath = q.get()
			p.join()
		if pickedPath is None:
			return {
				"data": None,
				"message":"Failed to select file"
			}, 404
		return {
			"data":pickedPath,
			"message":"Success"
		}, 200

api.add_resource(filePath, "/api/filepath")

class settings(Resource):
	def get(self):
		toReturn = {}
		with shelve.open(SHELF_NAME_SETTINGS, writeback=True) as shlf:
			toReturn.update({
				"wage-base-rate":shlf["WAGE_BASE_RATE"],
				"usual-hours":shlf["USUAL_HOURS"],
				"employee-name":shlf["EMPLOYEE_NAME"],
				"which-state-version":shlf["WHICH_AUSSTATE_VERSION"]
				})
		return {
			"data":toReturn,
			"message":"Success"
		}, 200

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("wage-base-rate")
		parser.add_argument("usual-hours")
		parser.add_argument("employee-name")
		parser.add_argument("which-state-version")
		parsed_args = parser.parse_args()
		with shelve.open(SHELF_NAME_SETTINGS, writeback=True) as shlf:
			wrong = {}
			if not (parsed_args["wage-base-rate"] is None) and parsed_args["wage-base-rate"].replace('.','').isnumeric():
				shlf["WAGE_BASE_RATE"] = float(parsed_args["wage-base-rate"])
			else:
				wrong.update({"Wage base rate":parsed_args["wage-base-rate"]})
			if not (parsed_args["usual-hours"] is None) and parsed_args["usual-hours"].isnumeric():
				shlf["USUAL_HOURS"] = float(parsed_args["usual-hours"])
			else:
				wrong.update({"Usual hours":parsed_args["usual-hours"]})
			if not (parsed_args["employee-name"] is None):
				shlf["EMPLOYEE_NAME"] = parsed_args["employee-name"]
			else:
				wrong.update({"Employee name":parsed_args["employee-name"]})
			legalStates = ["WA", "NT", "SA", "VIC", "NSW", "QLD", "ACT"]
			if not (parsed_args["which-state-version"] is None or (parsed_args["which-state-version"] not in legalStates)):
				shlf["WHICH_AUSSTATE_VERSION"] = parsed_args["which-state-version"]
			else:
				wrong.update({"State version":parsed_args["which-state-version"]})
		if not wrong == {}:
			returnS = "The following inputs were invalid: "
			for k,i in wrong.items():
				returnS += k + " (\'"+str(i)+"\'), "
			return {
				"data":None,
				"message":returnS[:-2] #trims last comma and space
			}
		return {
			"data":None,
			"message":"Successfully updated settings."
		}, 200

api.add_resource(settings, "/api/settings")

#--------------------------------

def start():
	if __name__ == "__main__":
		freeze_support()
		webbrowser.open('http://localhost:8000', new=1, autoraise=True)
		app.run(host='0.0.0.0', port="8000", debug=True)


start()