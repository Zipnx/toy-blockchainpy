
from typing import List

import struct
from binascii import hexlify, unhexlify
from hashlib import sha256
from dataclasses import dataclass

from coretc.crypto import data_sign, data_verify
from Crypto.PublicKey import ECC


@dataclass(init = True)
class UTXO:
    owner_pk: bytes
    amount: float

    index: int
    
    txid: bytes      = b''
    signature: bytes = b''
    
    def hash_sha256(self) -> bytes:
        '''
        Hash the UTXO object using SHA-256

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

    def to_json(self, is_input: bool = True) -> dict:
        '''
        Convert the UTXO into JSON

        Args:
            is_input (bool): Whether the UTXO will be used as an input

        Return:
            dict: Resulting JSON object

        '''
        
        json_data = {
            'owner': f'0x{sha256(self.owner_pk).hexdigest()}',
            'amount': self.amount,
            'index': self.index,
            'pk': hexlify(self.owner_pk).decode()
        }

        if is_input:
            json_data['unlock-sig'] = hexlify(self.signature).decode()
            json_data['txid'] = f'0x{hexlify(self.txid).decode()}' # im braindead


        return json_data
    
    @staticmethod
    def from_json(json_data: dict):
        '''
        Parse JSON representation of a UTXO into an object

        Args:
            json_data (dict): JSON data of a UTXO

        Return:
            UTXO: Resulting object
        '''

        is_input = 'unlock-sig' in json_data

        req_fields = ['pk', 'amount', 'txid', 'index'] # Owner is just for visualization not actually necessary

        for f in req_fields:
            if f not in json_data.keys(): return None

        return UTXO(
            owner_pk    = unhexlify(json_data['pk']),
            amount      = float(json_data['amount']),
            txid        = unhexlify(json_data['txid'][2:]),
            index       = int(json_data['index']),
            signature   = unhexlify(json_data['unlock-sig']) if is_input else b''
        )
    
    def get_signature(self, private_key: ECC.EccKey, outputs: List) -> bytes:
        '''
        Get the signature of the UTXO given a private key
        
        Return:
            bytes: Signature of the UTXO object
        '''

        # This is not ideal, since a SHA256 hash will be calculated again
        return data_sign( private_key, self.get_hash_with_outputs(outputs) ) or b'' 
    
    def sign(self, private_key: ECC.EccKey, outputs: List):
        '''
        Calculate and set the UTXO's signature then return the object itself

        Return:
            UTXO: Itself
        '''

        self.signature = self.get_signature(private_key, outputs)
        return self

    def unlock_spend(self, outputs: List) -> bool:
        '''
        Check if the signature is valid to unlock for a list of outputs

        Return:
            bool: Validity of the signature
        '''

        pub = ECC.import_key(self.owner_pk)

        return data_verify(pub, self.get_hash_with_outputs(outputs), self.signature)

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

        if not len(self.txid) == 32: return False
        if not self.signature: return False

        return True

    # trust me this is helpful
    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.index < other.index
    
    # will be needed for dicts
    def __hash__(self):
        return hash(self.hash_sha256())

