# Discrepancies

**Algorithm**

1. Iterate the two lists of dates included in this compare study, creating a master dates list
	- Store this list at the same level as "compare":object, as it contains information about both entries in that object.
	- Store it as "discrepancies":obj
1. Iterate the master dates list, and add an entry for each date into the discrepancies object.
	- Entries should be in the following format:

```json
{
	"compare": {...},
	"discrepancies": {
		"30-01-2023": {
			"badges": [
				{"Shift missing": description (string)},
				{"Pay rate different": description (string)},
				...
			],
			"highlights": [
				{"BASE HOURS":"rate"},
				{"BASE HOURS":"amount"},
				...
			]
		},
		...
	}
}
```


**Discrepancy Types**

- Shift missing
	- There is no matching shift in the other comparison list. This should only occur in isolation (as of course the rates/hours etc. will be different)
- Pay rate different
- Hours worked different
- Hour types different
- Day total different
	- If one of the above three discrepancies are present, this will neccessarily be included as well, as they all contribute to the day total. Thus, this is included for ease of rendering in the UI.