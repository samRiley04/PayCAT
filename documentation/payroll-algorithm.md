# analyseRoster Algorithm

**Contents**

- [Overview](#overview)
- [Global Variables](#global-variables)
- [analyseRoster - Overview](#analyseroster---overview)
- [analyseRoster - Preparation](#analyseroster---preparation)
- [analyseRoster - Checkpoints](#analyseroster---checkpoints)
- [analyseRoster - Creating pensList](#analyseroster---creating-penslist)
- [analyseRoster - Overtime](#analyseroster---overtime)
- [analyseRoster - Tidy Up](#analyseroster---tidy-up)

## Overview

This is a very complex function. You could argue it should be broken into more components to aid readability, but I was honestly not able to do better than I have done already. If you are reading this and your name isn't Sam, prepare yourself.

(I maintain that there is only ONE hacky workaround in this package.)

This is essentially replicating the logic that exists in HSS/Payroll's backend, used to calculate how much to pay you once being told your hours worked.

**Assumptions**
- You work 1FTE.
- Any hours in the input dictionary were accrued over a **14 day period.** (As you cannot calculate overtime rates without this assumption.)
- All hours _paid_ (not _worked_) contribute to your overtime threshold.
- There is only one penalty rate applied for working a public holiday.

**Limitations**

This function currently does not have the capacity to:
- Ingest on call hours (yet).
- Account for anyone <1FTE.
- Account for unrostered overtime. This should be entered into the roster manually as if it were your rostered hours. (i.e. extending your shift to include your overtime hours worked)

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

## Global Variables

Explanation of globally declared variables used in this package.

**To aid in selecting descriptions for certain pay rates:**
- `DESCRIPTORS_SHIFTS_PENS` (dict) - keys are used programmatically. Entries should be in the format "rate":"description" (e.g. "1.2":"PENALTIES AT 20%"). Prepend PH for public holiday descriptions.
- `DESCRIPTORS_SHIFTS_ALL` (dict) - keys are used programmatically as above. Prepend PH for public holiday descriptions. A superset containing the descriptors above and other non-penalty descriptors.

The differentiation between pens and non-pens descriptors is intentional. These dicts are used to store base/penalty rates correctly (see helper functions - `expandForBaseHours()`)

**To aid in calculating overtime:**
- `OVERTIME_RATES` (dict) - keys are used programatically. Entries should be in the format "cutoff":rate(float) (e.g. "80" or "55.5"). Cutoff means "after this many hours, pay any further hours at the given overtime rate"

**To aid in calculating penalties:**
- `PENALTY_RATES` (dict) - keys are used programatically. Entries should be in the format "Day of the week":(object), where the object contains entries in the format "cutoff":rate(float). Cutoff means "after this hour in a day, apply this penalty rate".
- `PENALTY_RATES_PH_GENERIC` (dict) - keys are used programatically. As above, except instead of a cutoff value keys are an offset value. Offset means "this many days after a public holiday, use this penalty rates object." REQUIRES: an entry with key="0".
- `PENALTY_RATES_PH` (dict) keys are used programatically. As above. This dict is filled dynamically with reference to `PENALTY_RATES_PH_GENERIC`.
- `PUBLIC_HOLIDAYS` (dict) keys are used programatically. As above. This dict is filled dynamically by `generatePublicHolidays()` in the format (date object):"description".

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
In code comments, marked as Section One

- `rangeLower` and `rangeUpper` are used to ensure the 'day-after' in nightshifts aren't missed. 
- Some parts of this code section are not used, but I am too scared to remove them.
- in `for date in daysWorking:`, public holiday dates are removed from the (copied) list of all public holidays IF you are already working on that public holiday. This is because that same list is iterated through straight afterwards, and used to generate public holiday _observed_ shifts (which by definition, occur on dates you are NOT working). Does that make sense?
- in `for date in daysWorking:`, note that a timedelta object is constructed to insert the penalty rates for the day after a public holiday. This timedelta is created using the _KEYS_ in `PENALTY_RATES_PH_GENERIC`. A reminder to ensure they are integers. (This also occurs in `for PH in P_H_COPY:`)
    - When creating the entry for the day _after_ a public holiday, `blendRatesDicts()` is used to ensure that after 8am when the public holiday ends, the correct penalty rates are paid.
- `tempDict` is sorted by date in these steps as public holiday observed shifts would have been added to the end of the dict. (more a formatting issue than anything else.)

## analyseRoster - Checkpoints

Refers to steps **4-5(i)**.
In code comments, marked as Section Two.

Checkpoints are (ideally) a way to genericise the code for payroll logic so it can be applied to different health services with only modification of a dictionary, and not logic.

Checkpoints are datetime objects at constant points throughout a day and delineate when there is a change in penalties paid during a day/week.

Example (for WA, weekdays Tue - Fri):
```
HOURS:      |0000       0800      1200     1800      2359|
CHECKPOINT? |  20% pens   |      0% pens     |   25% pens|
```

They are specific for the shift day, as they each include the date the shift occurs on (not just the times), and as such must be created dynamically for each shift worked. This is ideal, because actually not every shift will have a standard set of rates - sometimes public holidays are involved.

Other notes:
- `daysToCheck` list is used to ensure nightshifts work. As mentioned in (5)(i), they cover two days but are one shift.

## analyseRoster - Creating `pensList`

Refers to step **5(ii)**. In code comments, marked as Section Three.

This whole section works and every time I try to optimise it, it stops working correctly. So it stays bloated.

I've settled on this approach to deconstructing a shift into it's components of different penalty rates, but there may be other better ways.

In summary, the two "anchor" method is just a way to visualise breaking the whole shift down into blocks delineated by the entries in the checkpoints list (as in the above section).

When debugging errors in this section, I find that working through it with paper and a pen writing pseudocode is very helpful. It has mostly lead to me creating this abomnination however, so take that with a grain of salt.

Other notes:
- When referring to `PENALTY_RATES` and `PENALTY_RATES_PH`, note that the latter uses keys of (datetime date) objects, and the former uses (string)s representing days of the week.
- Note that the start and end shift times are only added as checkpoints when they would NOT be a duplicate with a penalty-rate checkpoint.
- In this section we account for a 'futile shift'. This is where you work on a public holiday for a very short amount of hours. You typically get 2.5x base for PH shifts, but in these 'futile' circumstances, this rate actually comes out to LESS than you would have earned if you didn't work, and got paid the public holiday observed rate (1x base). This can be calculated easily, and is done so here - `USUAL_HOURS/PH_TOTAL_RATE`. Where `USUAL_HOURS` is the hours you would work on "an ordinary working day", as this is how the Award defines what PH observed should be paid as. PH_TOTAL_RATE is the total multiplier applied to base rate, 2.5 as before. You can see that if you work ED and your usual hours are 10-hour shifts, you are only able to "tolerate" a shift as short as 4 hours before it's not worth coming in. (This is also a judgement decision, I'd rather get paid and not come in than come in and work 4 hours - I still had to come into work).

## analyseRoster - Overtime

Refers to steps **5(iii) and (iv)**. In code comments, marked as Section Four.

Broadly: at some point in this shift, you know you will cross the overtime hours threshold. Step through the list of penalty rates/hours objects, and check if they will bring you over the limit by checking hour quantity. If not, pass them through to the 'finalised' dictionary `tempPensList` unadulterated.

If they will bring you over, first add an entry with the remaining pre-OT hours at the original rate. Because no assumptions are made about potential shift length, it's entirely possible a single shift could cross multiple OT rate marks. (Practically impossible in WA, no one would every get paid to work 41 hours straight.) Regardless, the functionality is there - the different "strata" (aka what OT rates apply to what hour ranges) are stepped through and hours remaining in the shift object are allocated appropriately.

Other notes:
- I think this section is well designed.
- this section uses the helper function `getCorrectOTRates()`. 

## analyseRoster - Tidy Up

Refers to steps **5(v)-(viii)**. In code comments, marked as Section Five.

Yadda yadda yadda you don't stop yappin

