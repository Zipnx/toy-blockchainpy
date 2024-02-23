
from coretc.transaction import TX
from coretc.utxo import UTXO

from typing import List
from Crypto.PublicKey import ECC
from hashlib import sha256
from binascii import hexlify, unhexlify

# alot of this code is from the previous version, and there is more to port

class Wallet:

    def __init__(self, private_key: ECC.EccKey):

        self.sk: ECC.EccKey = private_key
        self.pk: ECC.EccKey = private_key.public_key()

        self.owned_utxos: List[UTXO] = []

    @staticmethod
    def generate():
        priv = ECC.generate(curve = 'P-256')

        return Wallet(private_key = priv)

    def balance(self) -> float:
        '''
        Get the total balance of this address

        Return:
            float: Sum of owned utxo coins
        '''

        total: float = 0

        for utxo in self.owned_utxos:
            total += utxo.amount

        return total
    
    def get_pk_bytes(self) -> bytes:
        '''
        Get the ECC pk in DER format

        Returns:
            bytes: DER format public key
        '''

        return self.pk.export_key(format = 'DER')

    def get_address_str(self) -> str:
        '''
        Get the wallets address in hex digest form

        Return:
            str: Address string
        '''

        return f'0x{sha256( self.get_pk_bytes() ).hexdigest()}'
