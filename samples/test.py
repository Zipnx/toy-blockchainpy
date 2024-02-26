
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from binascii import hexlify

import time, json

from coretc import Chain, Block, BlockStatus, mine_block

def sample_block(bc: Chain, prev: bytes = b'') -> Block:

    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    
    mine_block(blk, True)

    return blk

def main():

    chain: Chain = Chain()
    prev: Block = None

    for i in range(16):
        print(f'{f" Block #{i} ":=^20}')

        newblock = sample_block(chain)

        res = chain.add_block(newblock)
        
        print(f'Result: {res}')
        print(json.dumps(newblock.to_json(), indent = 4))
        
        if not res == BlockStatus.VALID: break 

        print(f'{"="*30}')

        if chain.forks is not None:
            chain.forks._display()

        print(f'{"="*30}')






if __name__ == '__main__':
    main()
