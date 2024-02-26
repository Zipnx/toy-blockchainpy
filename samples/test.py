
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from binascii import hexlify

import time, json

from coretc import Chain, Block, BlockStatus, mine_block

def main():

    chain: Chain = Chain()

    for i in range(8):
        print(f'{f" Block #{i} ":=^20}')

        blk = Block(chain.get_tophash(), int(time.time()), chain.get_top_difficulty(), b'', [])

        mine_block(blk)
        
        res: BlockStatus = chain.add_block(blk)

        print('Add block result:', res)

        print(json.dumps(blk.to_json(), indent = 4))

        if chain.forks is not None:
            chain.forks._display()

    

if __name__ == '__main__':
    main()
