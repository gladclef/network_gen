from random import randint
import os

def dir(filepath: str) -> str:
	return os.path.dirname(filepath)

def bool_prob(prob_yes_percent: int):
	if prob_yes_percent == 0:
		return False

	ival = randint(1, 100)
	return ival <= prob_yes_percent