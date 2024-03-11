
from typing import Type

from binascii import hexlify, unhexlify
from dataclasses import dataclass
from hashlib import sha256
import json
from Crypto.Util.number import long_to_bytes
from coretc import transaction

from coretc.difficulty import hashDifficulty, adjustDifficulty, getDifficultyTarget, checkDifficulty
from coretc.transaction import TX
from coretc.utils.generic import data_hexdigest, data_hexundigest

@dataclass(init = True)
class Block:
    previous_hash: bytes
    timestamp: int
    difficulty_bits: int
    nonce: bytes

    transactions: list[TX]

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
            self.nonce +
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
            'prev': data_hexdigest(self.previous_hash),
            'hash': data_hexdigest(self.hash_sha256()),
            'timestamp': self.timestamp,
            'difficulty': self.difficulty_bits,
            'txs': tx_json,
            'nonce': data_hexdigest(self.nonce)
        }
        
        return result
    
    @staticmethod
    def from_json(json_data: dict) -> object | None:
        '''
        Initialize a block object from JSON

        Args:
            json_data (dict): JSON data representing a Block

        Return:
            Block: New block object
        '''

        req_fields = ['prev', 'hash', 'timestamp', 'difficulty', 'txs', 'nonce']

        if not len(req_fields) == len(json_data.keys()): return None 

        for f in req_fields:
            if f not in json_data.keys():
                return None
        
        # Get the transactions as object
        if not isinstance(json_data['txs'], list): 
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
            transactions    = tx_objects
        )
