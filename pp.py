from payroll import *
import json
from datetime import datetime, timedelta

for key, val in generatePublicHolidays([2024]).items():
	print("{k} | {dow} | {v}".format(k=key, dow=key.strftime("%a"), v=val))


import holidays


# yearsList = range(2015,2030)
# au_holidays = holidays.AU(subdiv='WA',years=yearsList)
# for key in au_holidays.get_named("King's Birthday"):
# 	jeff.update({key:au_holidays[key]})
# for key in au_holidays.get_named("Queen's Birthday"):
# 	jeff.update({key:au_holidays[key]})

# replace = {}
# tds = list(jeff.keys())
# for key in sorted(tds):
# 	replace.update({key:jeff[key]})
# jeff = replace

# for key, val in jeff.items():
# 	print("{k} | {dow} | {v}".format(k=key, dow=key.strftime("%a"), v=val))
