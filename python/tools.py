from random import randint
import os
from typing import Optional, Callable, TypeVar

A = TypeVar('A')

def dir(filepath: str) -> str:
	return os.path.dirname(filepath)

def bool_prob(prob_yes_percent: int):
	if prob_yes_percent == 0:
		return False

	ival = randint(1, 100)
	return ival <= prob_yes_percent

def decode_next(sval: str, conversion: Optional[Callable[[str], A]] = None) -> tuple[A, str]:
	""" Used to decode the next value from a csv encoded string
	
	Arguments
	---------
	    sval: the csv encoded string
		conversion: a function that returns a converted value from the first part of the csv string
	
	Returns
	-------
	    Either a string value if conversion is None, or whatever type the conversion produces. """
	if len(sval) == "" or "," not in sval:
		parts = [sval, ""]
	else:
		parts = sval.split(",", maxsplit=1)

	if conversion != None:
		parts[0] = conversion(parts[0])
	return parts[0], parts[1]