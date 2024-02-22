
from binascii import hexlify
from dataclasses import dataclass
from hashlib import sha256
from Crypto.Util.number import long_to_bytes

from coretc.difficulty import hashDifficulty, adjustDifficulty, getDifficultyTarget, checkDifficulty

@dataclass(init = True)
class Block:
    previous_hash: bytes
    timestamp: int
    difficulty_bits: int
    nonce: bytes

    transactions: list

    # TODO: Also need to cache some stuff for TXs

    def hash_sha256(self) -> bytes:
        '''
        Get the block hash

        Returns:
            bytes: The SHA-256 hash of the block object
        '''
        
        # TODO: Needs hashing of TXs

        return sha256(
            self.previous_hash + 
            long_to_bytes(self.timestamp) + 
            long_to_bytes(self.difficulty_bits) + 
            self.nonce
        ).digest()
    
    def is_hash_valid(self) -> bool:
        '''
        Check the block's hash against the current difficulty target

        Returns:
            bool: Whether the current block hash is valid
        '''

        return checkDifficulty(self.hash_sha256(), self.difficulty_bits)

    def to_json(self) -> dict:
        '''
        Convert the Block object into json

        Returns:
            dict: Dict object of block data (json serializable)

        '''
            
        # Todo: Add TXs

        result: dict = {
            'prev': f'0x{hexlify(self.previous_hash).decode()}',
            'hash': f'0x{hexlify(self.hash_sha256()).decode()}',
            'timestamp': self.timestamp,
            'difficulty': self.difficulty_bits,
            'nonce': hexlify(self.nonce).decode()
        }
        
        return result

