import flask
from flask import Flask, redirect, url_for, render_template, flash, request, session, send_from_directory, current_app
from flask_restful import Resource, Api, reqparse, inputs
from multiprocessing import Process, Queue
from datetime import datetime, timedelta

import logging
import webbrowser
import requests
import shelve
import sys
import os

#My files.
import PayslipFunctions as pFx
import payroll
import utilities as ut

# Initialise
#To ensure this works packaged.
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    app = Flask("PayCAT", template_folder=template_folder)
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
#?Do YAML config.

def isConfigDone():
	with shelve.open(SHELF_NAME_SETTINGS) as shlf:
		if (shlf["WAGE_BASE_RATE"] is None) or (shlf["USUAL_HOURS"] is None):
			return False
	return True

@app.route("/")
def home():
	return render_template("index.html")

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
		# SAFETYCHECK
		if not isConfigDone():
			return {
				"data":None,
				"message":"Settings not yet configured."
			}, 503
		parser = reqparse.RequestParser()
		parser.add_argument("filePath")
		parser.add_argument("mode")
		# Optional
		parser.add_argument("filePath2")
		parser.add_argument("rosterType")
		parser.add_argument("employeeName")
		parser.add_argument("startDate")
		parser.add_argument("endDate")
		parsed_args = parser.parse_args()

		# CREATE VIEW MODE ---
		if parsed_args["mode"] == "view":
			try:
				if parsed_args["filePath"].endswith(".pdf"):
					shelfEntry = pFx.ingestPDF(parsed_args["filePath"])
				elif parsed_args["filePath"].endswith(".xlsx"):
					parsed_args["employeeName"] = "Samuel Riley"
					with shelve.open(SHELF_NAME_SETTINGS) as shlf:
						baseRate = shlf["WAGE_BASE_RATE"]
						usualHours = shlf["USUAL_HOURS"]
					dataDict = payroll.analyseRoster(pFx.ingestRoster(parsed_args["filePath"], parsed_args["employeeName"], "C", datetime.strptime("2023-01-30", "%Y-%m-%d"), datetime.strptime("2023-02-12", "%Y-%m-%d")), baseRate, usualHours)
					shelfEntry = {
						"employeeName": parsed_args["employeeName"],
						"employer": "Unknown",
						"totalPretaxIncome": ut.deepSumAmounts(dataDict),
						"payPeriodStart": "30-01-2023",
						"payPeriodEnding": "12-02-2023",
						"data": dataDict
					}
				else:
					return {
						"data": None,
						"message": "Wrong filetype. Accepts .pdf and .xlsx only at this stage."
					}, 422
				#Shed the leading directories
				fileNameShort = parsed_args["filePath"].split('/')[-1]
				newlyMadeID = None
				#Shelf save.
				with shelve.open(SHELF_NAME, writeback=True) as shlf:
					#Add candidate to shelf using the next unique ID
					newlyMadeID = str(shlf["_NEXT_ID"])
					shlf['_NEXT_ID'] += 1
					shelfEntry.update({
						"name":fileNameShort,
						"mode":"view"
						})
					shlf[newlyMadeID] = shelfEntry
					return {
						"data":shlf[newlyMadeID],
						"message":"Success"
					}, 201
			except (FileNotFoundError):
				return {
					"data": None,
					"message":"File not found."
				}, 404
		# CREATE COMPARE MODE ---
		elif parsed_args["mode"] == "compare":
			#Do some compare shit.
			print(parsed_args)
			return {}, 200
		else:
			#Unknown mode.
			return {
				"data":None,
				"message":"Unknown mode supplied."
			}, 404


api.add_resource(studiesDataList, "/api/studydata")

class studyData(Resource):
	def get(self, studyID):
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
			p = Process(target=ut.filePicker,args=(q,))
			p.start()
			pickedPath = q.get()
			p.join()
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
				"usual-hours":shlf["USUAL_HOURS"]
				})
		return {
			"data":toReturn,
			"message":"Success"
		}, 200

	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument("wage-base-rate")
		parser.add_argument("usual-hours")
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
		app.run(host='0.0.0.0', port="8000", debug=True)

#webbrowser.open('http://localhost:8000', new=1, autoraise=True)
start()