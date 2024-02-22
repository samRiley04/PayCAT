class NameNotFound(Exception):
	pass
	#Found no recognisable name in the roster. Is it spelled correctly?

class NoRecognisedDates(Exception):
	pass
	#Found no recognisable dates in the roster.

class Insurmountable(Exception):
	pass
	#Used when variables are configured wrong and the program unequivocally should NOT continue. Should not be caught.