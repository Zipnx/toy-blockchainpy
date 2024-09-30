
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, time
from copy import deepcopy

from coretc import Chain, Block, TX, UTXO, mine_block, Wallet
from coretc import ChainSettings, BlockStatus
from coretc.utils.generic import data_hexdigest, dump_json

def sample_block(bc: Chain, prev: bytes = b'') -> Block:

    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    

    #mine_block(blk, True)

    return blk

def main():

    chain = Chain(ChainSettings(debug_dont_save = True))

    a = Wallet.generate()
    b = Wallet.generate()
    
    a_reward = a.create_reward_transaction(chain.get_top_blockreward())

    #print(json.dumps(a_reward.to_json(), indent = 4))

    newblock = sample_block(chain) 
    newblock.transactions.append(a_reward) 
    mine_block(newblock) 
    

    res = chain.add_block(newblock)
    
    if res != BlockStatus.VALID: return
    
    #pain
    outputs = a_reward.get_output_references()
    a.owned_utxos += outputs
    
    a_send = a.create_transaction_single(b.get_pk_bytes(), 0.69)
    b_reward = b.create_reward_transaction(chain.get_top_blockreward())
    
    print(len(a_send.inputs[0].signature))

    #print(json.dumps(a_send.to_json(), indent = 4))
    
    #    A    |    B    |     BAL A     |     DIFF B    | 
    #  REWARD |         |  10 (+10)     |       0       | 
    #  SEND   | REWARD  |  9.31 (-0.69) | 10.69 (+10.69)|
    #
    #

    newblock = sample_block(chain)
    newblock.transactions.append(a_send)
    newblock.transactions.append(b_reward)
    mine_block(newblock)

    #print(json.dumps(newblock.to_json(), indent = 4))

    res = chain.add_block(newblock)
    
    if res != BlockStatus.VALID: return

    outputs = b_reward.get_output_references()
    b.owned_utxos += outputs

    outputs = a_send.get_output_references()
    b.owned_utxos += [outputs[0]]
    a.owned_utxos += [outputs[1]]
    
    print(a.balance())
    print(b.balance())
    
    if chain.forks is None: return

    chain.forks._display()

    test = chain.forks.get_tallest_leaf()

    chain.merge_all()

    #dump_json(chain.utxo_set.get_as_json())

if __name__ == '__main__':
    main()
