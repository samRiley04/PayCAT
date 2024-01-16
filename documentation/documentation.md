# API and Backend Documentation

Detailed here is information on:
- API calls
- ..

## PDFData

**Endpoints**

- `/api/PDFData` accepts GET, POST.
- `/api/PDFData/<pdfName>` accepts GET, DELETE.

**Usage**

All responses are wrapped as below:

```json
{
	"data": "The proper content of the response",
	"message": "Description of what occurred"
}
```

### CREATE a new payslip

This is called by the user when the select 'New -> payslip' in the web UI.

`POST /api/PDFData`

**Arguments**

- `"pdfName"` the LONG file location in the local directory (e.g. /Users/sam/Documents/payslip.pdf) 

```json
{
	"pdfName":"/Users/sam/Documents/payslip.pdf"
}
```

**Response**

- `201 CREATED`
- `404 NOT FOUND` if no file by that name was found
- `415 UNSUPPORTED MEDIA TYPE` if not sending a .pdf name.

Returns the created payslip dictionary inside the data key:
```json
{
	"data": {
        "02-10-2023": [
            {
                "description": "BASE HOURS",
                "units": "0.50",
                "rate": "43.8298",
                "amount": "21.91"
            },

...
```

### GET all currently registered payslips.

This is called when side-bar UI list is generated.

`GET api/PDFData`

**Response**

Returns a list of all KEYS (filenames) for payslips in the local database.

```json
{
	"data": [
		"payslip.pdf",
		"cgnm 123 0102",
		"cgnm 123 0103",

...
```

### GET data for a single registered payslip

This is called when the user clicks an entry in the side-bar UI.

`GET /api/PDFData/<file name.pdf>`

**Responses**

- `200 OK`
- `404 NOT FOUND` if no file by that name was found
- `415 UNSUPPORTED MEDIA TYPE` if not requesting a .pdf name.

Returns the dictionary of data for that key (payslip) in the local database.

```json
{
	"data": {
	    "02-10-2023": [
	        {
	            "description": "BASE HOURS",
	            "units": "0.50",
	            "rate": "43.8298",
	            "amount": "21.91"
	        },
	        {
	            "description": "PENALTIES AT 20%",
	            "units": "0.50",
	            "rate": "8.7660",
	            "amount": "4.38"
	        }
	   	],
...
```

### DELETE a single registered payslip

This is called when the user clicks the delete button next to a paylsip entry in the sidebar.

`DELETE /api/PDFData/<file name.pdf>`

**Responses**

- `204 NO CONTENT` if deleted successfully.
- `404 NOT FOUND` if no file by that name was found
- `415 UNSUPPORTED MEDIA TYPE` if not requesting a .pdf name.

