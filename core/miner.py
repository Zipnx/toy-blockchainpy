
from core.blocks import Block

import time, os, struct

def mine_block(blk: Block) -> None:
    '''
    Mine a block. Brute force the nonce until the hash is valid

    Args:
        blk (Block): The block to be mined

    Returns:
        None

    '''

    mixer = os.urandom(8)

    counter = 0

    t0 = time.time()

    while not blk.is_hash_valid():
        blk.nonce = mixer + struct.pack('Q', counter)
        counter += 1

    print(f'Block mined. TIME: {time.time() - t0:.3f} CYCLES: {counter}')


