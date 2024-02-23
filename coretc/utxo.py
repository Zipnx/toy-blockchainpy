
import struct
from binascii import hexlify, unhexlify
from hashlib import sha256
from dataclasses import dataclass

from coretc.crypto import data_sign, data_verify


@dataclass(init = True)
class UTXO:
    owner_pk: bytes
    amount: float

    txid: bytes
    index: int

    signature: bytes

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
            int.to_bytes(self.index) +
            self.signature
        ).digest()

    def to_json(self, is_input: bool = True) -> dict:
        '''
        Convert the UTXO into JSON

        Args:
            is_input (bool): Whether the UTXO will be used as an input

        Return:
            dict: Resulting JSON object

        '''
        
        # what tf was i thinking when i had this as 2 seperate functions
        json_data = {
            'owner': f'0x{sha256(self.owner_pk).hexdigest()}',
            'amount': self.amount,
            'txid': f'0x{hexlify(self.txid).decode()}',
            'index': self.index,
            'pk': hexlify(self.owner_pk).decode()
        }

        if is_input:
            json_data['unlock-sig'] = hexlify(self.signature).decode()

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

        

    # trust me this is helpful
    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.index < other.index
    
    # will be needed for dicts
    def __hash__(self):
        return hash(self.hash_sha256())
