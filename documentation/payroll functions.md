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

**Output**

Outputs a dictionary, where keys are dates and values are a list of all "hour-types" (BASE HOURS, OVERTIME @ 1.5) that occurred on that day. Each of the entries in the list is a object (dict) that has all the attributes you might want - description, units, rate, total amount for that hour-type.

This dictionary is then wrapped with more meta-information by app.py

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

NORTH METRO HEALTH SERVICE:
- 

**Helper functions**

**Algorithm**

Checkpoints are (ideally) a way to genericise the code for payroll logic so it can be applied to different health services with only modification of a .yaml or other file.

Checkpoints are datetime objects at constant points throughout a day and delineate when there is a change in penalties paid during a day/week.

Example (for North Metro Health Service):

WEEKDAYS:
HOURS:      |0000       0800      1200     1800      2359|
CHECKPOINT? |  20% pens   X      0% pens    X    25% pens|
