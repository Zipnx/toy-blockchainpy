
import unittest

from coretc import TX, UTXO, Wallet, Chain
from coretc import ChainSettings, BlockStatus

from coretc.blocks import Block
from coretc.miner import mine_block
from tests.helpers import create_empty_chain, create_example_block, create_example_tx, create_example_utxo

class TestTXValidation(unittest.TestCase):
    
    def test_block_reward(self) -> None:

        chain = create_empty_chain()
        a = Wallet.generate()

        self.assertEqual(a.balance(), 0)
        
        reward = a.create_reward_transaction(chain.get_top_blockreward() + 1)

        newblock = create_example_block(mine = False)
        newblock.transactions.append(reward)
        mine_block(newblock)

        res = chain.add_block(newblock)

        self.assertEqual(res, BlockStatus.INVALID_TX_WRONG_REWARD_AMOUNT)

        reward = a.create_reward_transaction(chain.get_top_blockreward())

        newblock = create_example_block(mine = False)
        newblock.transactions += [reward, reward]
        mine_block(newblock)

        res = chain.add_block(newblock)

        self.assertEqual(res, BlockStatus.INVALID_TX_MULTIPLE_REWARDS)

        newblock = create_example_block(mine = False)
        newblock.transactions += [reward]
        mine_block(newblock)

        res = chain.add_block(newblock)

        self.assertEqual(res, BlockStatus.VALID)

        a.owned_utxos.append(reward.outputs[0])

        self.assertEqual(a.balance(), chain.get_top_blockreward())

