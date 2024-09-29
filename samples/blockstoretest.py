
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc.blockstorage import BlockStorage
from coretc import Chain, Block, mine_block
from coretc.settings import ChainSettings
from coretc.utils.generic import dump_json, data_hexdigest

import time

def sample_block(bc: Chain, prev: bytes = b'') -> Block:
    print(f'Prev: {data_hexdigest(bc.get_tophash())}')
    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    

    mine_block(blk, True)

    return blk

def main():
    chain = Chain(settings = ChainSettings())
    
    print(chain.get_block_by_height(0))

    for i in range(5):
        print(f'{"="*10} BLOCK #{i + 1} {"="*10}')
        chain.add_block(sample_block(chain, chain.get_tophash()))
    
    chain.merge_all()

    store = BlockStorage('./data/blocks/', 8)

    store.store_blocks(chain.blocks)
    

if __name__ == '__main__': main()
