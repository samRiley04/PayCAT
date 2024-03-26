# How To Use PayCAT
___

Please note, this browser window is just a way for the program to display information. If you accidentally close it, the program will continue running. You can reopen any browser window and navigate to "http://localhost:8000" to continue using PayCAT.

This also means to close the program completely, you must close the "terminal" or "cmd" window that was opened when first running the program. It will have "PayCAT" in it's title bar.

You can use PayCAT by creating either a "Compare" mode study, or a "View" mode study.

## Table of Contents

- [Compare Mode](#using-compare-mode)
- [View Mode](#using-view-mode)
- [Exporting Data](#exporting-data)

## Using "Compare" Mode
___

Creating a Compare mode study shows you the **differences** between your payslip and roster, side by side.

To check your payslip in compare mode, you need:
- Your payslip in ".pdf" format
- Your roster in ".xlsx" format (an excel file)

**Currently supported payslip types:**
- WA Health payslips
- NT Government Health payslips (pending)

Most types of rosters are supported, including those that use letter-codes to represent shift times (e.g. JD = "0800-1700")

**Currently unsupported roster types:**
- Double-layered letter-code rosters such as the SCGH Emergency Department roster.
- Any rosters that do not contain the full date including year.

### Steps to Create a "Compare" Mode Study

1. Add a new study (Top bar -> "New")
1. In the compare mode (purple) column, click "choose file" and select your payslip.
1. Below that, click the other "choose file" and select your roster. Some extra options will appear because you have selected a roster file
1. Fill in the required details:
	- Roster type simply represents the general structure of your roster - click the "?" icon for representative photos. 
	- Your name - should be verbatim as it is written in the roster, including capital letters
	- Dates - should be the same dates that your payslip applies to
1. Click "Create Compare".

### Interpreting a "Compare" Mode Study

- The two boxes at the top (purple and red) are a summary of the payslip and roster files respectively. PPE means "pay period ending". They are labelled "payslip" (purple) or "roster" (red).
- Below this, alerts are listed. Alerts represent a significantly unusual discrepancy in one of the files. Typically this is something like the payslip/roster dates not aligning exactly with one another.
- Then we see the "Discrepancies" header. Below this is a row for every **date** that is **not identical** in both files. Click a row to expand them and read more.
	- The dark grey boxes above each row label each type of discrepancy that is recorded for that date. There may be multiple.
	- When expanded, a description for each discrepancy is listed below. The row also expands to show all the different pay rates that contributed to the total dollars earned that day.
	- Differences are highlighted yellow.
- Move through each date and try and identify why there may be differences between the payslip and roster.
- When you reach the end of "Discrepancies", there is another section labelled "Full Comparison" which shows every pay entry recorded in both files (not just ones that have discrepancies).

## Using "View" Mode
___

Creating a View mode study shows you a break down of a single roster or payslip. The main use for this is to quickly and simply calculate what you **should have been paid** for your roster. This could then be compared manually to a payslip later on. For payslips, they are summarised in a neater format than the PDF.

As above, most types of rosters are supported.

### Steps to Create a "View" Mode Study

1. Add a new study (Top bar -> "New")
1. In the view mode (blue) column, click "choose file" and select your file.
1. If you selected a roster, fill out the extra boxes as you would when creating a Compare mode study.
1. Click "Create View"

### Interpreting a "View" Mode Study

- Option 1: Manually check the study with a payslip that may be in a format incompatible with PayCAT.
- Option 2: Export the data from a roster opened with "View" mode (Top bar -> "Export" -> "EXCEL") and include it in a spreadsheet of your choosing.

## Exporting Data
___

Exporting is most useful for rosters "calculated" into hours and total dollar amounts. To export, click the study you want to export and go the the Top bar -> Export -> EXCEL or PDF.

When exporting a Compare study, it will export only the .xlsx (roster) file preferentially. If both or neither are rosters, it exports the left file. Don't ask. 

Recommended settings for PDF files:
- Print to PDF
- Macos: Select "Background graphics". Set "Scale" to "Customised" -> 50%.

**Notes for exporting**
- The program struggles with exporting payslips because there are many different types of random descriptions. It struggles to identify this and may throw errors.