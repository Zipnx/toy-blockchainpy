
from binascii import hexlify, unhexlify
from hashlib import sha256
from typing import List
from dataclasses import dataclass, field
import os, logging

from coretc.utxo import UTXO
from coretc.crypto import data_sign, data_verify
from coretc.utils.generic import data_hexdigest, data_hexundigest

logger = logging.getLogger('tc-core')

@dataclass(init = True)
class TX:
    inputs:  List[UTXO] = field(default_factory=list)
    outputs: List[UTXO] = field(default_factory=list)

    _nonce: bytes = b''
    _txid_cache: bytes = b'' # Used so the object is not hashed needlessly

    def hash_sha256(self) -> bytes:
        '''
        Hash the transaction using SHA256

        Return:
            bytes: Resulting 32 byte hash digest
        '''

        return sha256(
            hash_utxo_list(self.inputs + self.outputs) +
            self._nonce
        ).digest()
    
    def get_txid(self, ignore_cache: bool = False) -> bytes:
        '''
        Gets the transaction's current transaction ID

        Args:
            ignore_cache (bool): If true the hash will be recalculated even if it is already cached
        Return:
            bytes: The 32 byte hash
        '''
        
        if self._txid_cache and not ignore_cache: return self._txid_cache

        return self.hash_sha256()

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
            'nonce': data_hexdigest(self._nonce),
            'txid': data_hexdigest(self.get_txid())
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

        obj = TX(
            inputs      = res_ins,
            outputs     = res_out,
            _nonce      = data_hexundigest(json_data['nonce'])
        )
        
        if not json_data['txid'] == data_hexdigest(obj.hash_sha256()):
            logger.error('Deserialized TX does not have the same transaction ID')
            return None

        return obj

    def set_utxo_indexes(self) -> None:
        '''
        Sets the UTXO indexes in ascending order
        Invalidates the txid cache

        Return:
            None
        '''
        
        self._txid_cache = b''

        for i, utxo in enumerate(self.outputs):
            utxo.index = i
    
    def ingoing_funds(self) -> float:
        '''
        Get sum of all UTXO input fund amounts

        Return:
            float: Total in-going funds
        '''

        funds: float = 0.

        for utxo in self.inputs:
            funds += utxo.amount

        return funds

    def outgoing_funds(self) -> float:
        '''
        Get the sum of all UTXO output fund amounts

        Return:
            float: Total out-going funds
        '''

        funds: float = 0.

        for utxo in self.outputs:
            funds += utxo.amount

        return funds

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
    
    def gen_nonce(self) -> bytes:
        '''
        Generates a random nonce for the transaction
        Also invalidates the txid cache

        Return:
            bytes: The nonce bytes that have been set to the TX
        '''

        self._nonce = os.urandom(8)
        self.txid_cache = b''
        return self._nonce
    
    def make(self):
        '''
        Sets the UTXO indexes, generates a nonce and the transaction id
        
        Return:
            TX: Returns the object itself (reference ofc)
        '''

        self.set_utxo_indexes()
        self.gen_nonce()

        return self
    
    def is_valid(self) -> bool:
        '''
        Check if the nonce and txid is set
        NOTE: UTXOs are check using check_inputs & check_outputs
        '''

        if self._nonce == b'': return False
        
        return True

    def add_output(self, output: UTXO) -> None:
        '''
        Add the UTXO to the outputs and invalidate the cached txid
        '''
        self.outputs.append(output)
        self.txid_cache = b''

    def add_input(self, input: UTXO) -> None:
        '''
        Add the UTXO to the inputs and invalidate the cached txid
        '''
        self.inputs.append(input)
        self.txid_cache = b''

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
    
