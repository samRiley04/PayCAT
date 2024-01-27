# Roster Functions

This details important overview information about the ingestRoster() and its helper functions

## Scope

Covers the following functions:

```
|PayslipRosterFunctions.py
|-- IngestRoster()
|---- dateValidTypeA() **todo 
|---- dateValidTypeB()
|---- dateValidTypeC() **todo
|---- parseDate()
|---- parseHours()
...
```

## IngestRoster()

**Usage**

`IngestRoster(fileName, findName, rosterFormat, startDate, endDate)`

**Arguments**

- `fileName` (string) - the full system path to the file in question. Accepted file types: .xlsx
- `findName` (string) - the EXACT name of the employee as it appears in fileName
- `rosterFormat` (string, options="A", "B", "C") - defines the structure of the roster file (see below)
- `startDate` (datetime obj) - the start of the date range the function will return. (Inclusive)
- `endDate` (datetime obj) - the end of the date range the function will return. (Inclusive)

**Output**

Returns a dictionary with dates as keys, and strings of the worked shift as the value.

```json
{
	"2023-08-21": "1300-1900",
    "2023-08-22": "1300-1900",
    "2023-08-23": "1300-1900",
    "2023-08-24": "1300-1900",
    "2023-08-25": "0700-1900",
    "2023-08-27": "0800-1400"
}
```

**Helper functions**

- `dateValidType*()` - used to verify if a potential date found in the spreadsheet should actually be used to look for data cells (semantically valid). Three different functions for roster formats A, B, and C.
- `parseDate()` - used to check if a string is a technically valid date (i.e. fits the correct character pattern)
- `parseHours()` - used to check if a string is a technically valid set of hours (i.e. fits the correct character pattern)

## dateValidTypeA()

**Usage**

`if dateValidType(cell, sheet):`

**Arguments**

`cell` (pyopenxl cell object) - the cell whos value is the potential date in question.
`sheet` (pyopenxl sheet object) - the sheet that cell is contained in.

**Output**

Returns `True` or `False` according to the following algorithm:

- Does the cell have 


## dateValidTypeB()

**Usage**

**Arguments**

**Output**

## dateValidTypeC()

**Usage**

**Arguments**

**Output**
todo