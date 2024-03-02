
from binascii import hexlify, unhexlify
from hashlib import sha256
from typing import List
from dataclasses import dataclass
import os

from coretc.utxo import UTXO
from coretc.crypto import data_sign, data_verify

@dataclass(init = True)
class TX:
    inputs:  List[UTXO]
    outputs: List[UTXO]

    nonce: bytes = b''
    txid: bytes = b''

    def hash_sha256(self) -> bytes:
        '''
        Hash the transaction using SHA256

        Return:
            bytes: Resulting 32 byte hash digest
        '''

        return sha256(
            hash_utxo_list(self.inputs + self.outputs) +
            self.nonce
        ).digest()
    
    def to_json(self) -> dict:
        '''
        Serialize the TX into a JSON object

        Return:
            dict: Said json object
        '''

        in_json:  List[dict] = []
        out_json: List[dict] = []

        # TODO: Check for errors on these 2 fuckers
        for in_utxo in self.inputs:
            in_json.append(in_utxo.to_json(is_input = True))

        for out_utxo in self.outputs:
            out_json.append(out_utxo.to_json(is_input = False))
    
        return {
            'inputs': in_json,
            'outputs': out_json,
            'nonce': hexlify(self.nonce).decode(),
            'txid': f'0x{hexlify(self.txid).decode()}'
        }

    @staticmethod
    def from_json(json_data: dict):
        '''
        Get a TX object from its JSON form

        Args:
            json_data (dict): JSON data representing a tx

        Return:
            TX: Resulting TX object
        '''
        
        req_fields = ['inputs', 'outputs', 'nonce', 'txid']

        if not len(json_data.keys()) == len(req_fields): return None

        for f in req_fields:
            if f not in json_data.keys(): return None

        res_ins: List[UTXO] = []
        res_out: List[UTXO] = []
        
        in_json: List[dict] = json_data['inputs']
        out_json: List[dict] = json_data['outputs']

        if not isinstance(in_json, list) or not isinstance(out_json, list): return None

        # Parse the UTXO inputs

        for utxo_json in in_json:
            obj = UTXO.from_json(utxo_json)

            if obj is None: 
                #print('error in input deserialization')
                return None
            
            res_ins.append(obj)

        # now do the outputs

        for utxo_json in out_json:
            obj = UTXO.from_json(utxo_json)

            if obj is None: 
                #print('error in output deserialization')
                return None

            res_out.append(obj)

        return TX(
            inputs      = res_ins,
            outputs     = res_out,
            nonce       = unhexlify(json_data['nonce']),
            txid        = unhexlify(json_data['txid'][2:])
        )

    def set_utxo_indexes(self) -> None:
        '''
        Sets the UTXO indexes in ascending order

        Return:
            None
        '''
        
        for i, utxo in enumerate(self.outputs):
            utxo.index = i

    def check_outputs(self) -> bool:
        '''
        Check if the UTXO outputs are properly set up

        Return:
            bool: Whether the TX's outputs have distinct and valid indexes
        '''

        self.outputs.sort() # Using the __lt__ dunder method they are sorting by their index
        
        if len(self.outputs) > 255: return False

        for i, utxo in enumerate(self.outputs):

            if not utxo.is_valid(): return False

            if not utxo.index == i: return False 

        return True

    def gen_txid(self) -> bytes:
        '''
        Sets the transaction id to the current hash of the transaction 
        and at the same time returns it as a list of bytes

        This is necessary because the txid must be also set to the utxo outputs

        Return:
            bytes: The transaction id
        '''

        self.txid = self.hash_sha256()
        return self.txid
    
    def gen_nonce(self) -> bytes:
        '''
        Generates a random nonce for the transaction

        Return:
            bytes: The nonce bytes that have been set to the TX
        '''

        self.nonce = os.urandom(8)
        return self.nonce
    
    def make(self):
        '''
        Sets the UTXO indexes, generates a nonce and the transaction id
        
        Return:
            TX: Returns the object itself (reference ofc)
        '''

        self.set_utxo_indexes()
        self.gen_nonce()
        self.gen_txid()

        return self

    def check_inputs(self) -> bool:
        '''
        Check the utxo input validities also check the UTXO input 
        signatures to unlock for spending. Note this only checks for the case
        where all the inputs are from 1 address

        Return:
            bool: Whether the inputs are proper
        '''

        for utxo_input in self.inputs:

            if not utxo_input.is_valid_input(): return False
            
            if not utxo_input.unlock_spend(self.outputs): return False

        return True

def hash_utxo_list(lst: List[UTXO]) -> bytes:
    '''
    Collectively hash a list of utxos

    Args:
        lst (List[UTXO]): List of UTXOs to be hashed

    Return:
        bytes: Resulting 32 byte hash digest

    '''

    return sha256(
        b''.join([utxo.hash_sha256() for utxo in lst]) 
    ).digest()
    
