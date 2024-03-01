
from coretc.transaction import TX
from coretc.utxo import UTXO

from typing import List, Tuple, Literal
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

    def pick_utxo_inputs(self, amount: float, order: Literal['small', 'big']) -> Tuple[List[UTXO], float]:
        '''
        Return a list of owned utxos whose total worth is above the "amount"
        Can specify an "order" so that the smallest utxos are used
        
        Args:
            amount (float): Minimum value required
            order ("small" / "big"): Order by which owned utxos are picked

        Return:
            Tuple[List[UTXO], float]: The resulting list of UTXOs and their total value

        '''

        result: List[UTXO] = list()
        total_value: float = 0.

        self.owned_utxos.sort(key = lambda x: x.amount, reverse = (order == 'big'))

        for utxo in self.owned_utxos:
            result.append(utxo)
            total_value += utxo.amount

            if total_value > amount:
                break

        if total_value < amount:
            return [], -1

        return result, total_value

    def create_transaction_single(self, recv_pk: bytes, amount: float, order: Literal['small', 'big'] = 'small') -> TX | None:
        '''
        Create a transaction to a single receiver (also returns the change to the current address)

        Args:
            recv_pk (bytes): The receiver's public key bytes
            amount (float): The amount of funds to send
            order ("small" / "big"): Order by which the utxo's are picked, default is small

        Return:
            TX | None: The resulting transaction or None if it cannot be created
        '''

        used_inputs, funds = self.pick_utxo_inputs(amount, order)

        if funds < amount:
            return None

        outputs = list()
        outputs.append(UTXO(owner_pk = recv_pk, amount = amount, index = 0))
        
        if funds > amount:
            outputs.append(UTXO(owner_pk = self.get_pk_bytes(), amount = funds - amount, index = 1))

        for utxo in used_inputs:
            utxo.sign(self.sk, outputs)

        tx = TX(
            inputs = used_inputs,
            outputs  = outputs
        )
        tx.gen_nonce()
        tx.gen_txid()

        return tx

    def create_reward_transaction(self, reward: float) -> TX:
        '''
        Create a block reward transaction with this address as the sole rewardee

        Args:
            reward (float): The reward amount

        Return:
            TX: Resulting transaction
        '''

        tx = TX(
            inputs = [],
            outputs = [
                UTXO(owner_pk = self.get_pk_bytes(), amount = reward, index = 0)
            ]
        )

        tx.gen_nonce()
        tx.gen_txid()

        return tx
