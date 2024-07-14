
from typing import Type, Optional

from binascii import hexlify, unhexlify
from dataclasses import dataclass
from hashlib import sha256
import json, struct, logging
from Crypto.Util.number import long_to_bytes
from coretc import transaction

from coretc.difficulty import hashDifficulty, adjustDifficulty, getDifficultyTarget, checkDifficulty
from coretc.transaction import TX
from coretc.utils.generic import data_hexdigest, data_hexundigest

logger = logging.getLogger('tc-core')

@dataclass(init = True)
class Block:
    previous_hash: bytes
    timestamp: int
    difficulty_bits: int
    nonce: bytes


    transactions: list[TX]

    _VERSION: int = 1

    # TODO: Also need to cache some stuff for TXs

    def hash_sha256(self) -> bytes:
        '''
        Get the block hash

        Returns:
            bytes: The SHA-256 hash of the block object
        '''

        return sha256(
            self.previous_hash + 
            long_to_bytes(self.timestamp) + 
            long_to_bytes(self.difficulty_bits) + 
            self.nonce + struct.pack('B', self._VERSION) + 
            b''.join([tx.get_txid() for tx in self.transactions])
        ).digest()
    
    def is_hash_valid(self) -> bool:
        '''
        Check the block's hash against the current difficulty target

        Returns:
            bool: Whether the current block hash is valid
        '''

        return checkDifficulty(self.hash_sha256(), self.difficulty_bits)

    def to_json(self) -> dict[str, str | int | list]:
        '''
        Convert the Block object into json

        Returns:
            dict: Dict object of block data (json serializable)

        '''
        
        tx_json = []

        for tx in self.transactions:
            tx_json.append(tx.to_json())

        result: dict[str, str | int | list] = {
            'version': self._VERSION,
            'prev': data_hexdigest(self.previous_hash),
            'hash': data_hexdigest(self.hash_sha256()),
            'timestamp': self.timestamp,
            'difficulty': self.difficulty_bits,
            'txs': tx_json,
            'nonce': data_hexdigest(self.nonce)
        }
        
        return result
    
    @staticmethod
    def valid_block_json(json_data: dict) -> bool:
        '''
        Make sure the JSON form of a supposed block contains valid fields, in the proper
        forms

        Args:
            json_data (dict): The JSON data to be validated
        Returns:
            bool: Validity result
        '''

        # First check that all the fields are present
        req_fields = ['version','prev', 'hash', 'timestamp', 'difficulty', 'txs', 'nonce']

        if not len(req_fields) == len(json_data): return False

        for field in req_fields:
            if field not in json_data: return False

        ### Validate the individual field forms ###
        version = json_data['version']
        prevhash = json_data['prev']
        blockhash = json_data['hash']
        timestamp = json_data['timestamp']
        difficulty = json_data['difficulty']
        txs = json_data['txs']
        nonce = json_data['nonce']

        # Version is an int & 0 < VERSION < 256
        if not isinstance(version, int):
            if not str(version).isdigit(): return False
            json_data['version'] = int(version)

        if not int(version) > 0 and not int(version) < 256: return False

        # Prev & Current hash, 0x + 32 bytes (64 chars)
        if not isinstance(prevhash, str): return False
        if not prevhash[:2] == '0x': return False
        if not len(prevhash[2:]) == 64: return False

        if not isinstance(blockhash, str): return False
        if not blockhash[:2] == '0x': return False
        if not len(blockhash[2:]) == 64: return False
        

        # Timestamp is a 64 bit int
        if not isinstance(timestamp, int):
            if not str(timestamp).isdigit(): return False
            timestamp = int(timestamp)
            json_data['timestamp'] = timestamp

        if timestamp <= 0: return False
        if timestamp.bit_length() > 64: return False

        # Difficulty is a 32 bit int exactly
        

        if not isinstance(difficulty, int):
            if not str(difficulty).isdigit(): return False
            difficulty = int(difficulty)
            json_data['difficulty'] = difficulty

        if difficulty.bit_length() > 30: return False

        # TXs is a list
        if not isinstance(txs, list): return False

        # And the nonce is in hex format, max is 255 bytes 
        if not isinstance(nonce, str): return False
        if not nonce[:2] == '0x': return False
        if not len(nonce[2:]) < 511: return False

        if not len(nonce) < 256: return False

        return True

    @staticmethod
    def from_json(json_data: dict) -> Optional['Block']:
        '''
        Initialize a block object from JSON

        Args:
            json_data (dict): JSON data representing a Block

        Return:
            Block: New block object
        '''

        if not Block.valid_block_json(json_data): 
            logger.error('Invalid block JSON')
            return None
        

        tx_objects: list[TX] = []

        for transaction_json in json_data['txs']:
            obj: TX | None = TX.from_json(transaction_json)

            if obj is None: return None
            
            tx_objects.append(obj)


        return Block(
            previous_hash   = data_hexundigest(json_data['prev']),
            timestamp       = json_data['timestamp'],
            difficulty_bits = json_data['difficulty'],
            nonce           = data_hexundigest(json_data['nonce']),
            transactions    = tx_objects,
            _VERSION        = json_data['version']
        )
