
import math
from binascii import hexlify
from Crypto.Util.number import long_to_bytes, bytes_to_long

# Most of this code is from the old project, TODO: need to document it and or refactor

def hashDifficulty(diffBits: int) -> int:
    '''
    Get the estimated cycles needed to mine a hash with the given target difficulty bits

    Return:
        int: Difficulty count
    '''
    return int(getDifficultyTarget(0x20FFFFFF) / getDifficultyTarget(diffBits))

def getDifficultyTarget(diffBits: int) -> int:
    '''
    Get the difficulty target value, ie the value which the hash must be lesser than

    Return:
        int: Difficulty target
    '''

    exp = (diffBits & 0xFF000000) >> 24
    bits = diffBits & 0x00FFFFFF

    return int( bits * ( 256 ** (exp - 3) ) )


def checkDifficulty(hash: bytes, difficulty: int) -> bool:
    '''
    Check if a given hash's value is under the target difficulty, making it valid

    Return:
        bool: Hash's validity
    '''

    #hashValue = int(hexlify(hash), 16)
    hashValue = bytes_to_long(hash) # better 

    return hashValue < getDifficultyTarget(difficulty)

# When i wrote this i was SEVERELY sleep deprived at 4am with my blood pressure reaching unhuman levels, when i wrote this only god and i understood what i was doing, now, only god knows
# nvm i kinda get it
def adjustDifficulty(diffBits: int, change: float) -> int:
    '''
    Lower/Increade the difficulty target given a % difference

    Return:
        int: New difficuty bits
    '''
    change = max(0.50, change)
    change = min(2.00, change)
    change = 1/change
    
    exp = (diffBits & 0xFF000000) >> 24  
    val = diffBits & 0x00FFFFFF

    newValue = val * change
    newExponent = exp

    newValue = int(newValue)
    
    if newValue > 0xFFFFFF:
        # It gets too big, increase the exponent by 1 to use the next MSB (byte), and fuck the least on
        newExponent += 1

        newValue >>= 8
        
    
    elif math.floor(newValue) <= 0xFFFF:
        
        newExponent -= 1
        newValue <<= 8
    
    if newValue == 0: newValue = 1

    return min( (int(newExponent) << 24) | int(newValue), 0x20FFFFFF)



