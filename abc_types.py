from dataclasses import dataclass
from enum import Enum

class Sentiment(Enum):
	POS = 'positive'
	NEG = 'negative'
	NEUTRAL = 'neutral'