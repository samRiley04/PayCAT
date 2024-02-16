# API and Backend Documentation

Detailed here is information on:
- Studydata API (interacting with the database containing study entries for payslips or rosters.)
- Settings API (interacting with the database containing settings for the web application and studydata functions.) *TODO*
- Other API endpoints (includes `filePath`) *TODO*

## Studydata

**Endpoints**

- `/api/studydata` accepts GET, POST.
- `/api/studydata/<id>` accepts GET, DELETE.

**Usage**

All responses are wrapped as below:

```json
{
	"data": "The proper content of the response",
	"message": "Description of what occurred"
}
```

### CREATE a new study entry

This is called by the user when the select 'New -> payslip' in the web UI.

`POST /api/studydata`

**Arguments**

All arguments are provided as strings.

- `mode`: options are `view` or `compare` mode - determines how the two files are displayed.
- `filePath` and `filePath2`: the LONG file location in the local directory (e.g. /Users/sam/Documents/payslip.pdf) (include the second filePath only in `compare` mode)
- `rosterType` and `rosterType2`: if the provided file is a roster, what format is it laid out in? See roster functions. (include a second roster type only in `compare` mode)
- `startDate` and `endDate`: the start and end dates for which to ingest the given files, in the given in the DD-MM-YYYY format. (include the second pair of dates only in `compare` mode)

```json
{
	"mode":"compare",
    "filePath":"/Users/sam/Documents/GitHub/PayCAT/test.pdf",
    "filePath2":"/Users/sam/Documents/GitHub/PayCAT/TESTING/OPH.xlsx",
    "rosterType2":"C",
    "employeeName2":"Samuel Riley",
    "startDate2":"30-01-2023",
    "endDate2":"12-02-2023"
}
```

**Response**

- `201 CREATED`
- `404 NOT FOUND` if no file by that name was found or an invalid mode argument given.
- `415 UNSUPPORTED MEDIA TYPE` if not sending a .pdf name.
- `503 SERVICE UNAVAILABLE` if the settings for the server are not yet configured. See documentation on the settings API.

Returns the created payslip dictionary as either `"view":<object>` or `"compare":<list of two objects>`.

E.g. View mode

``` json
{
    "data": {
        "view": {
            "name": "test.pdf",
            "employeeName": "RILEY,SAMUEL NATHAN ",
            "employer": "NORTH METROPOLITAN HEALTH SERVICE",
            "totalPretaxIncome": "5,142.58",
            "payPeriodStart": "04-06-2023",
            "payPeriodEnding": "18-06-2023",
            "data": {...}
        }
    }
}
```

E.g. Compare mode

```json
{
    "data": {
        "compare": [
            {
                "name": "test.pdf",
                "employeeName": "RILEY,SAMUEL NATHAN ",
                "employer": "NORTH METROPOLITAN HEALTH SERVICE",
                "totalPretaxIncome": "5,142.58",
                "payPeriodStart": "04-06-2023",
                "payPeriodEnding": "18-06-2023",
                "data": {...}
            },
            {
                "name": "OPH.xlsx",
                "employeeName": "Samuel Riley",
                "employer": "Unknown",
                "totalPretaxIncome": "3,888.97",
                "payPeriodStart": "30-01-2023",
                "payPeriodEnding": "12-02-2023",
                "data": {...}
            }
       	]
    }
}
```

### GET all currently recorded studies.

This is called when side-bar UI list is generated.

`GET /api/studydata`

**Response**

Returns the entire local database of studies in the format `<id>:<data>`.

```json
{
	"data": {
		"18": {
			"view": {...}
		},
		"22": {
			"compare": [...]
		},
		...
	}
}
```

### GET data for a single registered study

This is called when the user clicks an entry in the side-bar UI.

`GET /api/studydata/<id>`

**Responses**

- `200 OK`
- `404 NOT FOUND` if no file by that name was found

Returns the dictionary of data for that id in the local database.

```json
{
	"data": {
		"view": {
			"name": "test.pdf",
            "employeeName": "RILEY,SAMUEL NATHAN ",
            "employer": "NORTH METROPOLITAN HEALTH SERVICE",
            "totalPretaxIncome": "5,142.58",
            "payPeriodStart": "04-06-2023",
            "payPeriodEnding": "18-06-2023",
            "data": {...}
		}
	}
}
```

### DELETE a single registered payslip

This is called when the user clicks the delete button next to a paylsip entry in the sidebar.

`DELETE /api/studydata/<id>`

**Responses**

- `204 NO CONTENT` if deleted successfully.
- `404 NOT FOUND` if no file by that name was found
- `503 SERVICE UNAVAILABLE` if the settings for the server are not yet configured. See documentation on the settings API.

