
from binascii import hexlify, unhexlify
from copy import deepcopy
from hashlib import sha256
import json
from typing import List, Optional
from dataclasses import dataclass, field
import os, logging
from coretc.object_schemas import TX_JSON_SCHEMA, is_schema_valid
from coretc.utils.errors import deprecated

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

    def get_output_references(self) -> list[UTXO]:
        '''
        Get a list of the outputs with the transaction id set n stuff

        Return:
            list[UTXO]: UTXO Output list
        '''

        result: list[UTXO] = []

        for utxo in self.outputs:
            ref_obj = deepcopy(utxo)

            ref_obj.txid = self.get_txid()

            result.append(ref_obj)

        return result

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

            if not in_utxo.is_valid_input():
                logger.warning('Invalid UTXO Input being converted to JSON')
                break

            in_json.append(in_utxo.to_json(is_input = True))

        for out_utxo in self.outputs:
            
            if not out_utxo.is_valid():
                logger.warning('Invalid UTXO Output being converted to JSON')
                break

            out_json.append(out_utxo.to_json(is_input = False))
    
        return {
            'inputs': in_json,
            'outputs': out_json,
            'nonce': data_hexdigest(self._nonce),
            'txid': data_hexdigest(self.get_txid())
        }
    
    @staticmethod
    def valid_transaction_json(json_data: dict) -> bool:
        '''
        Validate the schema of a tx object in JSON form

        Args:
            json_data (dict): TX in json form

        Returns:
            bool: Whether its valid or not
        '''

        return is_schema_valid(json_data, TX_JSON_SCHEMA)

    @staticmethod
    def from_json(json_data: dict) -> Optional['TX']:
        '''
        Get a TX object from its JSON form

        Args:
            json_data (dict): JSON data representing a tx

        Return:
            TX: Resulting TX object
        '''
        
        if not TX.valid_transaction_json(json_data): return None

        res_ins: List[UTXO] = []
        res_out: List[UTXO] = []
        
        in_json: List[dict] = json_data['inputs']
        out_json: List[dict] = json_data['outputs']

        # Parse the UTXO inputs

        for utxo_json in in_json:
            obj = UTXO.from_json(utxo_json)

            if obj is None: 
                #print('******************** error in input deserialization')
                return None
            
            res_ins.append(obj)

        # now do the outputs

        for utxo_json in out_json:
            obj = UTXO.from_json(utxo_json)

            if obj is None: 
                #print('************************** error in output deserialization')
                return None

            res_out.append(obj)

        result: TX | None = TX(
            inputs      = res_ins,
            outputs     = res_out,
            _nonce      = data_hexundigest(json_data['nonce'])
        )

        
        if result is None:
            logger.error('Error creating TX object from JSON data')
            return None

        if not json_data['txid'] == data_hexdigest(result.hash_sha256()):
            logger.error('Deserialized TX does not have the same transaction ID')
            logger.error(f'Invalid txid: {data_hexdigest(result.hash_sha256())}')


            #logger.error(json.dumps(result.to_json()['outputs'], indent = 4))
            #logger.error(f'New utxo hash: {data_hexdigest(result.outputs[0].hash_sha256())}')
            #logger.error(result.outputs[0])

            return None

        return result
    
    @deprecated
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
        
    def transaction_fee(self) -> float:
        '''
        Get the amount of tokens that the miner can claim as a fee
        (Unaccounted ingoing funds)

        Returns:
            float: Amount of tokens claimable by miners
        '''

        return self.ingoing_funds() - self.outgoing_funds()

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

        self.gen_nonce()

        return self
    
    def is_valid(self) -> bool:
        '''
        Check if the nonce is set
        NOTE: UTXOs are check using check_inputs & check_outputs
        '''

        if self._nonce == b'': return False
        
        return True

    def add_output(self, output: UTXO) -> None:
        '''
        Add the UTXO to the outputs and invalidate the cached txid
        '''

        if len(self.outputs) == 0:
            output.index = 0
        else:
            output.index = self.outputs[-1].index + 1

        self.outputs.append(output)
        self.txid_cache = b''

    def add_outputs(self, outputs: List[UTXO]) -> None:
        for utxo in outputs:
            self.add_output(utxo)

    def add_input(self, input: UTXO) -> None:
        '''
        Add the UTXO to the inputs and invalidate the cached txid
        '''
        self.inputs.append(input)
        self.txid_cache = b''

    def add_inputs(self, inputs: List[UTXO]) -> None:
        for utxo in inputs:
            self.add_input(utxo)

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
    
