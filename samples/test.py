
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from rich import print_json
from coretc import Chain, ChainSettings, Block, BlockStatus, mine_block
from coretc.utils.generic import data_hexdigest

def sample_block(bc: Chain, prev: bytes = b'') -> Block:

    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    
    mine_block(blk, True)

    return blk

def main():
    
    os.system('rm ./data/blocks/*.dat')

    chain: Chain = Chain(ChainSettings())

    #print(data_hexdigest(chain.get_tophash()))
     
    for i in range(90):
        print(f'{f" Block #{i+1} ":=^20}')
        if i+1 > 60:
            input(f'Enter to mine block {i+1}')

        newblock = sample_block(chain)
        
        res = chain.add_block(newblock)
        
        print_json(data = newblock.to_json())

        if not res == BlockStatus.VALID: break 
    

    #chain.forks._display()
    chain.save()


if __name__ == '__main__':
    main()
