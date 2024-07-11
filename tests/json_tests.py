
from coretc import Block, TX, UTXO
import unittest

from coretc.utils.generic import dump_json
from coretc.wallet import Wallet
from tests.helpers import create_example_block, create_example_tx, create_example_utxo

class TestJsonConversion(unittest.TestCase):

    def test_simple_block_json(self) -> None:
         
        blk: Block = create_example_block()

        blk_json = blk.to_json()

        blk_copy = Block.from_json(blk_json)

        self.assertFalse(blk_copy is None, "Error deserializing JSON to Block object")
        
        if blk_copy is not None:
            self.assertEqual(blk.hash_sha256(), blk_copy.hash_sha256(), 
                            "Block and it's copy don't have the same hash")

    def test_simple_tx_json(self) -> None:

        tx: TX = create_example_tx().make()

        tx_json = tx.to_json()

        tx_copy: TX | None = TX.from_json(tx_json)

        self.assertFalse(tx_copy is None, "Error deserializing JSON to TX object")

        if tx_copy is not None:
            self.assertEqual(tx.hash_sha256(), tx_copy.hash_sha256(),
                             "TX and it's copy don't have the same transaction ID")
    def test_simple_utxo_json(self) -> None:

        utxo: UTXO = create_example_utxo()
        utxo_json = utxo.to_json()

        utxo_copy: UTXO | None = UTXO.from_json(utxo_json)

        self.assertFalse(utxo_copy is None, "Error deserializing JSON to UTXO object")

        if utxo_copy is not None:
            self.assertEqual(utxo.hash_sha256(), utxo_copy.hash_sha256(),
                             "UTXO and it's copy don't have the same hash")

    def test_tx_with_utxos(self) -> None:
        
        test_wallet_a = Wallet.generate()
        tx = test_wallet_a.create_reward_transaction(0.5)

        self.assertIsNotNone(tx, 'Error creating TX')

        tx_json = tx.to_json()

        tx_copy: TX | None = TX.from_json(tx_json)

        self.assertFalse(tx_copy is None, 'Error deserializing JSON to TX object')
        
        if tx_copy is None: return

        self.assertEqual(tx.hash_sha256(), tx_copy.hash_sha256(), 
                        "Transaction and it's copy have different transaction IDs")

        self.assertEqual(len(tx.inputs), len(tx_copy.inputs),
                         "Transaction and it's copy have differnet inputs")

        self.assertEqual(len(tx.outputs), len(tx_copy.outputs),
                         "Transaction and it's copy have different outputs")
        
        self.assertFalse(tx_copy.outputs[-1].signature,
                         "Output UTXO has a signature?")

if __name__ == '__main__':
    unittest.main()
