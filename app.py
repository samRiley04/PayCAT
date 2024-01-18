import flask
from flask import Flask, redirect, url_for, render_template, flash, request, session, send_from_directory, current_app
from flask_restful import Resource, Api, reqparse, inputs
from multiprocessing import Process, Queue

import logging
import webbrowser
import requests
import shelve
import sys
import os

#My files.
import PayslipFunctions as pFx
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
with shelve.open(SHELF_NAME, writeback=True) as shlf:
	if not "_NEXT_ID" in shlf:
		shlf["_NEXT_ID"] = 1
#?Do YAML config.

@app.route("/")
def home():
	return render_template("index.html")

# ------–––– API ------––––

class PDFDataList(Resource):
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
		#Dead On Arrival POST request - simply a cue to open the file picker locally.

		#Unfortunately neccessary to create an entire subprocess just to use tkinter (as it *must* be run in the main process.)
		#Then uses a Queue the file path back to the main process.
		pdfNameLong = ""
		if __name__ == "__main__":
			q = Queue()
			p = Process(target=ut.filePicker,args=(q,))
			p.start()
			pdfNameLong = q.get()
			p.join()
		# Check validity
		if not pdfNameLong[-4:] == ".pdf":
			return {
				"data":None,
				"message":"Incorrect file type - pdfs only!"
			}, 415
		# Try to find the file.
		try:
			shelfEntry = pFx.ingestPDF(pdfNameLong)
			#Shed the leading directories
			fileNameShort = pdfNameLong.split('/')[-1]
			newlyMadeID = None
			#Shelf save.
			with shelve.open(SHELF_NAME, writeback=True) as shlf:
				"""
					REDUNDANT - don't need to uniqufy these anymore as data is stored under IDs now.
					if fileNameShort in shlf:
						#Attempt to unique-ify the name. This may be unsuccessful, thus the second loop check.
						filesTrueName = fileNameShort[:-4] #trim the .pdf
						fileNameShort = filesTrueName + "(1).pdf"
						indx = 1
						#Did that unique-ifying work?
						while fileNameShort in shlf:
							#No? Ok keep iterating.
							indx += 1
							fileNameShort = filesTrueName + "(" + str(indx) + ").pdf"
				"""
				#Add candidate to shelf using the next unique ID
				newlyMadeID = str(shlf["_NEXT_ID"])
				shlf['_NEXT_ID'] += 1
				shelfEntry.update({
					"name":fileNameShort,
					"type":"view"
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


api.add_resource(PDFDataList, "/api/PDFData")

class PDFData(Resource):
	def get(self, pdfID):
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
				toReturn = shlf[pdfID]
			except (KeyError):
				return {
					"data":None,
					"message":"File not found."
				}, 404
		return {
			"data":toReturn,
			"message":"Success"
		}, 200

	def delete(self, pdfID):
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			if pdfID in shlf:
				shlf.pop(pdfID)
				return {
					"data":None,
					"message":"Success"
				}, 204
			else:
				return {
					"data":None,
					"message":"Could not find file by that name."
				}, 404

api.add_resource(PDFData, "/api/PDFData/<string:pdfID>")

class FilePath(Resource):
	#Kinda counter intuitive - but GET the path because the application creates the file selector popup and gives the info back to the user.
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

api.add_resource(FilePath, "/api/FilePath")

#--------------------------------

def start():
	if __name__ == "__main__":
		app.run(host='0.0.0.0', port="8000", debug=True)

#webbrowser.open('http://localhost:8000', new=1, autoraise=True)
start()