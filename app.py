from tkinter import Tk     
from tkinter import filedialog as fd     
from tkinter.filedialog import askopenfilename

import flask
from flask import Flask, redirect, url_for, render_template, flash, request, session, send_from_directory, current_app
from flask_restful import Resource, Api, reqparse, inputs


import logging
import webbrowser
import requests
import shelve

#My files.
import PayslipFunctions as pFx

# Initialise
app = Flask("PayCAT")
logging.basicConfig(filename='server.log', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S%p')
api = Api(app)
#SHELF
SHELF_NAME = "PayCAT-shelf"
#?Do YAML config.

@app.route("/")
def home():
	return render_template("navbar.html")

# ------–––– API ------––––

class PDFDataList(Resource):
	def get(self):

		filename = ""
		filename = askopenfilename()
		root.withdraw()
		if filename == "":
			root.mainloop()
		else:
			root.destroy()

		# Get rid of this when shelf established. Its wrong.
		#return pFx.ingestPDF('test2.pdf'), 200
		keysList = []
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			for key in shlf:
				keysList.append(key)

		return {
			"data":keysList,
			"message":"Success"
		}, 200


	# Get given a valid local filename, and then generate+store a psDict using that filename
	# Return the psDict just created (would just be calling GET anyway.)
	def post(self):
		parser = reqparse.RequestParser()
		# e.g. pdfName = "/Users/sam/Documents/payslip.pdf"
		parser.add_argument("pdfName")
		parsed_args = parser.parse_args()
		# Check validity
		if not parsed_args["pdfName"][-4:] == ".pdf":
			return {
				"data":None,
				"message":"Incorrect file type - pdfs only!"
			}, 415

		jeff = selectFile()
		print(jeff)

		return 1, 200

		# Try to find the file.
		try:
			newPsDict = pFx.ingestPDF(parsed_args["pdfName"])
			#Shed the leading directories
			fileNameShort = parsed_args["pdfName"].split('/')[-1]
			print("Short filename: "+fileNameShort)
			#Shelf save.
			with shelve.open(SHELF_NAME, writeback=True) as shlf:
				
				if fileNameShort in shlf:
					#Attempt to unique-ify the name. This may be unsuccessful, thus the second loop check.
					filesTrueName = fileNameShort[:-4] #trim the .pdf
					fileNameShort = filesTrueName + "(1).pdf"
					indx = 1
					#Did that unique-ifying work?
					while fileNameShort in shelf:
						#No? Ok keep iterating.
						indx += 1
						fileNameShort = filesTrueName + "(" + str(indx) + ").pdf"
				
				#Add candidate to shelf.
				shlf[fileNameShort] = newPsDict
			return {
				"data":newPsDict,
				"message":"Success"
			}, 201
		except (FileNotFoundError):
			return {
				"data": None,
				"message":"File not found."
			}, 404

	#pdfNameShort is the filename minus all directories it's in.
	def delete(self, pdfNameShort):
		#If in shelf, delete it.
		return 200


api.add_resource(PDFDataList, "/api/PDFData")

class PDFData(Resource):
	def get(self, pdfNameShort):
		# Validate.
		if not pdfNameShort[-4:] == ".pdf":
			return {
				"data":None,
				"message":"Incorrect file type - pdfs only!"
			}, 415
		toReturn = {}
		# Retrieve that entry from the shelf if it exists.
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			try:
				toReturn = shlf[pdfNameShort]
			except (KeyError):
				return {
					"data":None,
					"message":"File not found."
				}, 404
		return {
			"data":toReturn,
			"message":"Success"
		}, 200

	def delete(self, pdfNameShort):
		if not pdfNameShort[-4:] == ".pdf":
			return {
				"data":None,
				"message":"Incorrect file type - pdfs only!"
			}, 415
		with shelve.open(SHELF_NAME, writeback=True) as shlf:
			if pdfNameShort in shlf:
				shlf.pop(pdfNameShort)
				return {
					"data":None,
					"message":"Success"
				}, 204
			else:
				return {
					"data":None,
					"message":"Could not find file by that name."
				}, 404

api.add_resource(PDFData, "/api/PDFData/<string:pdfNameShort>")



#--------------------------------

def start():
	if __name__ == "__main__":
		root = Tk()
		app.run(host='0.0.0.0', port="8000", debug=True)

#webbrowser.open('http://localhost:8000', new=1, autoraise=True)
start()