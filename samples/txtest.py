
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, time
from copy import deepcopy

from coretc import Chain, Block, TX, UTXO, mine_block, Wallet
from coretc import ChainSettings, BlockStatus
from coretc.utils.generic import data_hexdigest

def sample_block(bc: Chain, prev: bytes = b'') -> Block:

    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    

    #mine_block(blk, True)

    return blk

def main():

    chain = Chain(ChainSettings())

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
    rew_output = deepcopy(a_reward.outputs[0])
    rew_output.txid = a_reward.get_txid()
    a.owned_utxos += [rew_output]
    
    a_send = a.create_transaction_single(b.get_pk_bytes(), 0.69)
    b_reward = b.create_reward_transaction(chain.get_top_blockreward())

    #print(json.dumps(a_send.to_json(), indent = 4))
    
    

    newblock = sample_block(chain)
    newblock.transactions.append(a_send)
    newblock.transactions.append(b_reward)
    mine_block(newblock)

    #print(json.dumps(newblock.to_json(), indent = 4))

    res = chain.add_block(newblock)

    for _ in range(8):
        newblock = sample_block(chain)
        mine_block(newblock)

        chain.add_block(newblock)

    print(chain.utxo_set.get_as_json())

if __name__ == '__main__':
    main()
