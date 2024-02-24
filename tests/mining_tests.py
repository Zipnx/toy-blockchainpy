
import unittest

from coretc import Block, UTXO, mine_block
from binascii import hexlify

from tests.helpers import create_example_block, create_example_utxo



class TestBlockMining(unittest.TestCase):

    def test_mine_basic(self):

        blk: Block = create_example_block()
        blk.difficulty_bits = 0x20000FFF

        mine_block(blk)

        self.assertEqual(hexlify(blk.hash_sha256())[:3], b'000',
                         "Mined block's hash does not correspond to the difficulty_bits")
