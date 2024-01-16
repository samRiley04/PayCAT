from tkinter import Tk
from tkinter import filedialog as fd
from tkinter.filedialog import askopenfilename

Tk().withdraw()
#filename = askopenfilename(filetypes=[("PDF document",".pdf")]) 
filename = fd.askopenfile()
print(filename)