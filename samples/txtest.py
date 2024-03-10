
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json, time

from coretc import Chain, Block, TX, UTXO, mine_block, Wallet
from coretc import ChainSettings, BlockStatus

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
    

    newblock = sample_block(chain) 
    newblock.transactions.append(a_reward) 
    mine_block(newblock) 

    print(json.dumps(newblock.to_json(), indent = 4))


if __name__ == '__main__':
    main()
