
from enum import IntEnum

class BlockStatus(IntEnum):
    INVALID_PREVHASH = -1
    INVALID_DIFFICULTY = -2
    INVALID_POW = -3
    INVALID_DUPLICATE = -4
    
    INVALID_TX_MULTIPLE_REWARDS = -5
    INVALID_TX_INVALID_REWARD = -6
    INVALID_TX_WRONG_REWARD_AMOUNT = -7
    INVALID_TX_INPUTS = -8
    INVALID_TX_OUTPUTS = -9
    INVALID_TX_UTXO_IS_SPENT = -10
    INVALID_TX_AMOUNTS = -11
    INVALID_TX_MOD_UTXO = -12

    INVALID_ERROR = 0

    VALID = 1

    # Alternative VALID for when checking TX stuff
    # Ideally these would be different enums or i would just not have named it BlockStatus
    TX_VALID = 2
