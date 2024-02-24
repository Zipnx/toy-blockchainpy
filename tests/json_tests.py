
from coretc import Block, TX, UTXO
import unittest

from tests.helpers import create_example_block, create_example_tx, create_example_utxo

class TestJsonConversion(unittest.TestCase):

    def test_simple_block_json(self):
         
        blk: Block = create_example_block()

        blk_json = blk.to_json()

        blk_copy: Block | None = Block.from_json(blk_json)

        self.assertFalse(blk_copy is None, "Error deserializing JSON to Block object")
        
        if blk_copy is not None:
            self.assertEqual(blk.hash_sha256(), blk_copy.hash_sha256(), 
                            "Block and it's copy don't have the same hash")

    def test_simple_tx_json(self):

        tx: TX = create_example_tx()
        tx.gen_nonce()
        tx.gen_txid()

        tx_json = tx.to_json()

        tx_copy: TX | None = TX.from_json(tx_json)

        self.assertFalse(tx_copy is None, "Error deserializing JSON to TX object")

        if tx_copy is not None:
            tx_copy.gen_txid()
            self.assertEqual(tx.txid, tx_copy.txid,
                             "TX and it's copy don't have the same transaction ID")
    def test_simple_utxo_json(self):

        utxo: UTXO = create_example_utxo()
        utxo_json = utxo.to_json()

        utxo_copy: UTXO | None = UTXO.from_json(utxo_json)

        self.assertFalse(utxo_copy is None, "Error deserializing JSON to UTXO object")

        if utxo_copy is not None:
            self.assertEqual(utxo.hash_sha256(), utxo_copy.hash_sha256(),
                             "UTXO and it's copy don't have the same hash")

    def test_tx_with_utxos(self):

        tx: TX = create_example_tx()
        
        a: UTXO = create_example_utxo()
        a.amount = 0.2

        b: UTXO = create_example_utxo()
        b.amount = 0.3
        b.index = 1

        c: UTXO = create_example_utxo()
        b.amount = 0.5

        tx.inputs  += [a, b]
        tx.outputs += [c]

        tx.gen_nonce()
        tx.gen_txid()

        tx_json = tx.to_json()

        tx_copy: TX | None = TX.from_json(tx_json)

        self.assertFalse(tx_copy is None, 'Error deserializing JSON to TX object')
        
        if tx_copy is None: return

        
        tx_copy.gen_txid()
        self.assertEqual(tx.txid, tx_copy.txid, 
                        "Transaction and it's copy have different transaction IDs")

        self.assertEqual(len(tx.inputs), len(tx_copy.inputs),
                         "Transaction and it's copy have differnet inputs")

        self.assertEqual(len(tx.outputs), len(tx_copy.outputs),
                         "Transaction and it's copy have different outputs")
        
        self.assertFalse(tx_copy.outputs[-1].signature,
                         "Output UTXO has a signature?")

if __name__ == '__main__':
    unittest.main()
