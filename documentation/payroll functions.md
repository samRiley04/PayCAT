# Payroll Functions

This details important overview information about the analyseRoster()

## Scope

Covers the following functions within `payroll.py`

- [analyseRoster()](#analyseroster)

## analyseRoster()

**Usage**

`analyseRoster(rosterDict)`

**Arguments**

- `rosterDict` (dictionary) - contains a set of dates and shift-times. (see output from ingestRoster())
- `debug` (Boolean) - show a plethora of print statements to assist debugging.

**Output**

Outputs a dictionary, where keys are dates and values are a list of all "hour-types" (e.g. BASE HOURS, OVERTIME @ 1.5) that occurred on that day. Each of the entries in the list is a object (dict) that has attributes such as description, units, rate, and total amount for that hour-type.

Generic form:

```json
{
    "date":list[
        dict{
            "description":string,
            "units":string
            "rate":string
            "amount":string
        },
        ...
    ],
    ...
}

```

Example:

```json
{
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
    "03-10-2023": [
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
}
```

**Payroll Rules (The Award)**

This function relies on a lot of idiosyncratic rules that are different for different employers. They define when overtime is paid, what value penalties are given for which periods, when public holidays are and how they are paid.

For this version I used: [Medical practitioners AMA industrial agreement 2022](https://www.health.wa.gov.au/~/media/Corp/Documents/Health-for/Industrial-relations/Awards-and-agreements/Doctors/Medical-practitioners-AMA-industrial-agreement-2022.pdf)

For reference of public holidays in WA I used the document above, as well as [Dept. Commerce - Public holidays in Western Australia](https://www.commerce.wa.gov.au/labour-relations/public-holidays-western-australia)

**Algorithm**

See payroll-algorithm.md

**Helper functions**

