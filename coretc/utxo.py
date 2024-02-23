
import struct
from binascii import hexlify
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

    def to_json_input(self) -> dict:
        '''
        Convert the UTXO into JSON for use as an INPUT

        Return:
            dict: Resulting JSON object

        '''

        return {
            'owner': f'0x{sha256(self.owner_pk).hexdigest()}',
            'amount': self.amount,
            'txid': f'0x{hexlify(self.txid).decode()}',
            'index': self.index,
            'unlock-sig': hexlify(self.signature).decode(),
            'pk': hexlify(self.owner_pk).decode()
        }
    
    def to_json_output(self) -> dict:
        '''
        Convert the UTXO into JSON for use as an OUTPUT
        (doesn't have an unlock signature)

        Return:
            dict: Resulting JSON object
        '''

        return {
            'owner': f'0x{sha256(self.owner_pk).hexdigest()}',
            'amount': self.amount,
            'txid': self.txid,
            'index': self.index,
            'pk': hexlify(self.owner_pk).decode()
        }
    
    # trust me this is helpful
    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self.index < other.index
    
    # will be needed for dicts
    def __hash__(self):
        return hash(self.hash_sha256())
