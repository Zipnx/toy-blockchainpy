
import unittest
from coretc import Wallet, TX, UTXO, BlockStatus

from tests.helpers import create_chain_block, create_example_tx, create_empty_chain

class TXSecurity(unittest.TestCase):
    
    def setUp(self) -> None:
        self.chain = create_empty_chain()
        
        self.a = Wallet.generate()
        self.b = Wallet.generate()
        self.c = Wallet.generate()

        self.BLK_REW = self.chain.settings.initial_blockreward

    def test_txsecurity_1(self) -> None:
        
        '''
        1) Test that a block with multiple reward transactions is rejected
        2) Wallet A gets rewarded
        '''

        self.assertEqual(self.a.balance(), 0., 'Wallet A has a non-zero balance')
        self.assertEqual(self.b.balance(), 0., 'Wallet B has a non-zero balance')
        self.assertEqual(self.c.balance(), 0., 'Wallet C has a non-zero balance')

        rew_a = self.a.create_reward_transaction(self.BLK_REW)
        rew_b = self.b.create_reward_transaction(self.BLK_REW)

        block = create_chain_block(self.chain, txs = [rew_a, rew_b])
        
        prev_height = self.chain.get_height()
        res = self.chain.add_block(block)

        self.assertEqual(res, BlockStatus.INVALID_TX_MULTIPLE_REWARDS, 'TX With multiple rewards was accepted?')

        self.assertEqual(prev_height, self.chain.get_height(), 'Height changed even though the block was not officially added?')

        block = create_chain_block(self.chain, txs = [rew_a])

        res = self.chain.add_block(block)

        self.assertEqual(res, BlockStatus.VALID, 'Block should have been added.')
        self.assertEqual(self.chain.get_height(), 1, 'Height should be one now')


