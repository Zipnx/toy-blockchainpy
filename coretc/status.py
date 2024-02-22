
from enum import IntEnum

class BlockStatus(IntEnum):
    INVALID_PREVHASH = -1
    INVALID_DIFFICULTY = -2
    INVALID_POW = -3

    VALID = 1
