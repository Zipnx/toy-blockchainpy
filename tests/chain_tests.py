
import unittest

from coretc import Chain, ForkBlock
from coretc import ChainSettings, BlockStatus

from coretc.blocks import Block
from tests.helpers import create_example_block 

class TestChain(unittest.TestCase):

    def test_block_addition(self) -> None:

        chain = Chain(ChainSettings())
        
        self.assertEqual(chain.get_tophash(), b'\x00'*32,
                         'Empty chain\'s tophash must be a null hash')

        newblock = create_example_block()
        res = chain.add_block(newblock)
        
        self.assertEqual(res, BlockStatus.VALID,
                         'Error adding genesis block to chain')
        self.assertEqual(chain.get_tophash(), newblock.hash_sha256(),
                         'Error adding genesis block to chain')

        self.assertEqual(len(chain.blocks), 0,
                         'New block added directly to the block list?')

        chain.merge_all()

        self.assertEqual(len(chain.blocks), 1,
                         'Genesis block shouldve been forcefully merged')
        self.assertEqual(chain.get_height(), 1)

        self.assertIsNone(chain.forks, 
                          'After forceful merge the chain forks should be none')

        self.assertEqual(chain.get_tophash(), newblock.hash_sha256(),
                         'After force merge the tophash is invalid?')

        newblock2 = create_example_block(prev = chain.get_tophash())

        res = chain.add_block(newblock2)
        
        self.assertEqual(res, BlockStatus.VALID)
        self.assertIsNotNone(chain.forks)

        if chain.forks is None: return

        self.assertEqual(len(chain.blocks), 1)
        self.assertEqual(chain.forks.get_tree_height(), 1)

        chain.merge_all()

        self.assertIsNone(chain.forks)
        self.assertEqual(len(chain.blocks), 2)
        self.assertEqual(chain.get_height(), 2)

    def test_block_denial(self) -> None:

        chain = Chain(ChainSettings())

        newblock = create_example_block(prev = b'\x69'*32)

        res = chain.add_block(newblock)

        self.assertNotEqual(res, BlockStatus.VALID)
        self.assertEqual(chain.get_height(), 0)
        self.assertEqual(chain.get_tophash(), b'\x00'*32)

        newblock = create_example_block(mine = False)
        newblock.difficulty_bits = 0x20FFFFFF

        res = chain.add_block(newblock)

        self.assertNotEqual(res, BlockStatus.VALID)
