# analyseRoster Algorithm

## Overview

This is a very complex function. You could argue it should be broken into more components to aid readability, but I was honestly not able to do better than I have done already. If you are reading this and your name isn't Sam, prepare yourself.

(I maintain that there is only ONE hacky workaround in this package.)

**Assumptions**
- You work 1FTE.
- Any hours in the input dictionary were accrued over a **14 day period.** (As you cannot calculate overtime rates without this assumption.)
- All hours _paid_ (not _worked_) contribute to your overtime threshold.
- There is only one penalty rate applied for working a public holiday.

**Limitations**

This function currently does not have the capacity to:
- Ingest on call hours.
- Account for anyone <1FTE.
- Account for unrostered overtime.

A quick refresher:

**Input**

- `rosterDict` (dictionary) - contains a set of dates and shift-times. (see output from ingestRoster())

e.g.
```json
{
    "2024-12-20": "0830-1630",
    "2024-12-21": "0830-1630",
    "2024-12-22": "0830-1630",
    "2024-12-23": "0830-1630",
    "2024-12-24": "0830-1630",
    "2024-12-25": "0830-1630",
    "2024-12-26": "0830-1630",
    "2024-12-27": "0730-1630",
    "2024-12-28": "0830-1630",
    "2024-12-29": "0830-1630",
    "2024-12-30": "0830-1230"
}
```

**Output**
```json
{
    "20-12-2024": [
        {
            "description": "BASE HOURS",
            "units": "8.0",
            "rate": "42.3298",
            "amount": "338.64"
        }
    ],
    "21-12-2024": [
        {
            "description": "BASE HOURS",
            "units": "8.0",
            "rate": "42.3298",
            "amount": "338.64"
        },
        {
            "description": "PENALTIES AT 50%",
            "units": "8.0",
            "rate": "21.1649",
            "amount": "169.32"
        }
    ],
	...
}
```

**Contents**

todo

## Global Variables

**To aid in selecting descriptions for certain pay rates:**
- `DESCRIPTORS_SHIFTS_PENS` (dict) - keys are used programmatically. Entries should be in the format "rate":"description" (e.g. "1.2":"PENALTIES AT 20%"). Prepend PH for public holiday descriptions.
- `DESCRIPTORS_SHIFTS_ALL` (dict) - keys are used programmatically as above. Prepend PH for public holiday descriptions. A superset containing the descriptors above and other non-penalty descriptors.

The differentiation between pens and non-pens descriptors is intentional. These dicts are used to store base/penalty rates correctly (see helper functions - `expandForBaseHours()`)

**To aid in calculating overtime:**
- `OVERTIME_RATES` (dict) - keys are used programatically. Entries should be in the format "cutoff":rate(float) (e.g. "80" or "55.5"). Cutoff means "after this many hours, pay any further hours at the given overtime rate"

**To aid in calculating penalties:**
- `PENALTY_RATES` (dict) - keys are used programatically. Entries should be in the format "Day of the week":(object), where the object contains entries in the format "cutoff":rate(float). Cutoff means "after this hour in a day, apply this penalty rate".
- `PENALTY_RATES_PH_GENERIC` (dict) - keys are used programatically. As above, except instead of a cutoff value keys are an offset value. Offset means "this many days after a public holiday, use this penalty rates object."
- `PENALTY_RATES_PH` (dict) keys are used programatically. As above. This dict is filled dynamically with reference to `PENALTY_RATES_PH_GENERIC`.
- `PUBLIC_HOLIDAYS` (dict) keys are used programatically. As above. This dict is filled dynamically by `generatePublicHolidays()`

**Other variables:**
- `WAGE_BASE_RATE` (float). Employee's base wage.
- `USUAL_HOURS` (int). Used for observed public holiday calculations. See 35.(4) in [Medical practitioners AMA industrial agreement 2022](https://www.health.wa.gov.au/~/media/Corp/Documents/Health-for/Industrial-relations/Awards-and-agreements/Doctors/Medical-practitioners-AMA-industrial-agreement-2022.pdf)
- `PH_TOTAL_RATE` (float). Used for observed public holiday calculations. Equals the total multiplier onto base rate when working public holiday hours (2.5 in WA).

## analyseRoster - Overview

This is the main function.

Refer to Global Variables or Common Scoped Variables for more information on variables mentioned in brief below.

Summary of the steps in this function, in approximate order:
1. Create another version of rosterDict that contains the same information, but using datetime objects for ease of use. (`tempDict`)
1. Iterate through the public holidays dict as well as the input dictionary. Note all PH that you are already rostered on for, and add a placeholder shift for ones that you aren't.
1. For each of the cases above, make an entry into `PENALTY_RATES_PH` with a penalty-rates object.
1. Define `runningHoursTotal`, which keeps track of all hours parsed. It is the counter which determines when overtime starts being paid.
1. Iterate through `tempDict`, and construct the dictionary `returnDict`. For each shift:
	1. Generate a list of penalty-rate checkpoints that occur during the day/s worked (night shifts are considered one shift but cover two days.
	1. Iterate through these checkpoints using a two-variable "crawling"-type method and construct a list `pensList`.
		1. Piece by piece, add entries to `pensList` containing a given number of hours and their associated penalty rate, and description.
		1. Take into account public holidays by referring to either of `PENALTY_RATES` or `PENALTY_RATES_PH`, as determined by the shift's date.
	1. Check if you have already crossed the overtime threshold, or, if with the addition of this shift's hours, we will.
	1. If overtime is applicable:
		1. Iterate through `pensList` and create a new list of penalties `tempPensList` which has penalty rates replaced with overtime rates, _where appropriate_ (e.g. Sunday rates are higher than overtime rates. Do not replace these.)
			- Complicated section. Utilises `getCorrectOTRates()`.
		1. Replace `pensList` with this new `tempPensList` (as it is most correct.)
	1. Tidy up the entries in `pensList`. Due to the way it was created, there may be multiple entries for a given pay rate for this single shift. Collate them using `tidyAndCollatePensList()` for ease of reading later on.
	1. Using `expandForBaseHours()`, iterate through `pensList` and make an additional entry for each _penalty rate_ (but not OT or PH rate). These entries are the base rate parts represented by the pens rates values in `PENALTY_RATES`. (See section below for full explanation.)
	1. Iterate through `pensList` and construct one final list (`pensListProper`) containing all the information in `pensList`, but wrapped formally/pretty in dicts as defined in the function documentation. Calculate dollar value pay rates and amounts here also. 
	1. Attach this formal `pensListProper` to `returnDict` and return this value.

## analyseRoster - Preparation

Notes on steps **1-3**.

- `rangeLower` and `rangeUpper` are used to ensure the 'day-after' in nightshifts aren't missed. 
- Some parts of this code section are not used, but I am too scared to remove them.
- in `for date in daysWorking:`, public holiday dates are removed from the (copied) list of all public holidays IF you are already working on that public holiday. This is because that same list is iterated through straight afterwards, and used to generate public holiday _observed_ shifts (which by definition, occur on dates you are NOT working). Does that make sense?
- in `for date in daysWorking:`, note that a timedelta object is constructed to insert the penalty rates for the day after a public holiday. This timedelta is created using the _KEYS_ in `PENALTY_RATES_PH_GENERIC`. A reminder to ensure they are integers. (This also occurs in `for PH in P_H_COPY:`)
- `tempDict` is sorted by date in these steps as public holiday observed shifts would have been added to the end of the dict. (more a formatting issue than anything else.)

## analyseRoster - Checkpoints

Refers to steps **4-?**.

Checkpoints are (ideally) a way to genericise the code for payroll logic so it can be applied to different health services with only modification of a dictionary, and not logic.

Checkpoints are datetime objects at constant points throughout a day and delineate when there is a change in penalties paid during a day/week.

Example (for WA, weekdays Tue - Fri):
```
HOURS:      |0000       0800      1200     1800      2359|
CHECKPOINT? |  20% pens   |      0% pens     |   25% pens|
```

Other notes:
- `daysToCheck` list is used to ensure nightshifts work. As mentioned in (5)(i), they cover two days but are one shift.
- When referring to `PENALTY_RATES` and `PENALTY_RATES_PH`, note that the latter uses keys of (datetime date) objects, and the former uses (string)s representing days of the week.


