
from typing import List, Optional

import struct, logging
from binascii import hexlify, unhexlify
from hashlib import sha256
from dataclasses import dataclass

from coretc.object_schemas import UTXO_IN_JSON_SCHEMA, UTXO_OUT_JSON_SCHEMA, is_schema_valid
from coretc.utils.generic import data_hexdigest, data_hexundigest, dump_json
from coretc.crypto import data_sign, data_verify
from Crypto.PublicKey import ECC

logger = logging.getLogger('tc-core')

@dataclass(init = True)
class UTXO:
    owner_pk: bytes
    amount: float

    index: int          = 0 
    txid: bytes         = b''
    signature: bytes    = b''
    
    def hash_sha256(self) -> bytes:
        '''
        Hash the UTXO object using SHA-256
        WARNING: Does no checks on the parameters themselves

        Return:
            bytes: 32 byte hash digest
        '''

        return sha256(
            self.owner_pk +
            struct.pack('f', self.amount) +
            self.txid +
            int.to_bytes(self.index)
        ).digest()
    

    def get_hash_with_outputs(self, outputs: List) -> bytes:
        '''
        Get the hash of the UTXO and it's outputs

        Return:
            bytes: SHA256 Hash digest
        '''

        output_hashes = b''.join( [utxo.hash_sha256() for utxo in outputs] )
        return sha256(
            output_hashes + self.hash_sha256() # Yes this is not ideal
        ).digest()
 
    def get_id(self) -> str:
        '''
        Retrieve the UTXO's identifier, defined as it's source txid and the index in the outputs

        Return:
            str: The utxo id string
        '''
        
        if not len(self.txid) == 32:
            logger.error('Unable to get utxo id, transaction id not set.')
            return ''

        return f'{data_hexdigest(self.txid, no_prefix = True)}:{self.index}'

    def to_json(self, is_input: bool = True) -> dict:
        '''
        Convert the UTXO into JSON

        Args:
            is_input (bool): Whether the UTXO will be used as an input

        Return:
            dict: Resulting JSON object

        '''
        
        json_data = {
            'owner': data_hexdigest(sha256(self.owner_pk).digest()),
            'amount': self.amount, # This doesn't need to be present on inputs, but im keeping it for easy display idc
            'index': self.index,
            'pk': hexlify(self.owner_pk).decode()
        }

        if is_input:
            json_data['unlock-sig'] = hexlify(self.signature).decode()
            json_data['txid'] = data_hexdigest(self.txid) # im braindead


        return json_data
    
    @staticmethod
    def valid_input_json(json_data: dict) -> bool:
        '''
        Whether a JSON object of a utxo input is valid
        '''
        return is_schema_valid(json_data, UTXO_IN_JSON_SCHEMA)

    @staticmethod
    def valid_output_json(json_data: dict) -> bool:
        '''
        Whether a JSON object of a utxo output is valid
        '''
        return is_schema_valid(json_data, UTXO_OUT_JSON_SCHEMA)

    @staticmethod
    def from_json(json_data: dict) -> Optional['UTXO']:
        '''
        Parse JSON representation of a UTXO into an object

        Args:
            json_data (dict): JSON data of a UTXO

        Return:
            UTXO: Resulting object
        '''

        is_input = 'unlock-sig' in json_data and 'txid' in json_data
        
        if is_input:
            if not UTXO.valid_input_json(json_data): return None
        else:
            if not UTXO.valid_output_json(json_data): return None

        return UTXO(
            owner_pk    = unhexlify(json_data['pk']),
            amount      = float(json_data['amount']),
            index       = int(json_data['index']),
            txid        = data_hexundigest(json_data['txid']) if is_input else b'',
            signature   = data_hexundigest(json_data['unlock-sig']) if is_input else b'' 
        )
    
    def get_signature(self, private_key: ECC.EccKey, outputs: List) -> bytes:
        '''
        Get the signature of the UTXO given a private key
        
        Return:
            bytes: Signature of the UTXO object
        '''

        # This is not ideal, since a SHA256 hash will be calculated again
        return data_sign( private_key, self.get_hash_with_outputs(outputs) ) or b'' 

    def sign(self, private_key: ECC.EccKey, outputs: List) -> 'UTXO':
        '''
        Calculate and set the UTXO's signature then return the object itself

        Return:
            UTXO: Itself
        '''

        self.signature = self.get_signature(private_key, outputs)
        logger.debug('Signed utxo input hash: ' + data_hexdigest(self.get_hash_with_outputs(outputs)))
        #dump_json(self.to_json())
        #print('Output count:', len(outputs))

        return self

    def unlock_spend(self, outputs: List) -> bool:
        '''
        Check if the signature is valid to unlock for a list of outputs

        Return:
            bool: Validity of the signature
        '''

        pub = ECC.import_key(self.owner_pk)

        if not (res := data_verify(pub, self.get_hash_with_outputs(outputs), self.signature)):
            logger.warning(f'Invalid sig of utxo input: {self.get_id()}')
        
            #dump_json(self.to_json())
        #print('Output count:', len(outputs))

        return res

    def is_valid(self) -> bool:
        '''
        Check if the UTXO's standard parameters (pk, amount, index) ie ones that
        are always necessary whether it's an input or output are valid
        
        Return:
            bool: Structural validity of the UTXO
        '''

        if not len(self.owner_pk) == 91: return False
        if self.amount <= 0: return False
        if self.index < 0 or self.index > 255: return False

        return True
    
    def is_valid_input(self) -> bool:
        '''
        To the validity checks for when this is used as an input, ie:
        The signature that is necessary to unlock the funds
        And the TXID it's referring to, where the UTXO was created.
        DOES NOT VERIFY THE SIGNATURE

        Return:
            bool: Structural validity of the UTXO's input parameters
        '''
        
        if not self.is_valid(): return False
        if not len(self.txid) == 32: return False
        if not self.signature: return False

        return True

    def compare_as_input(self, other) -> bool:
        '''
        Compare the UTXO object with another

        Args:
            other (UTXO): Other UTXO object
        Return:
            UTXO: Whether the UTXOs are the same as inputs
        '''
        
        if not self.txid == other.txid: return False
        if not self.index == other.index: return False
        if not self.amount == other.amount: return False
        if not self.owner_pk == other.owner_pk: return False

        return True

    # trust me this is helpful
    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.index < other.index
    
    # will be needed for dicts
    def __hash__(self):
        return hash(self.hash_sha256())
    
    # WARNING: This works only on INPUTS
    def __eq__(self, other):
        return self.get_id() == other.get_id() and isinstance(other, type(self))

