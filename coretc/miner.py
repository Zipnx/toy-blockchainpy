
from coretc.blocks import Block

import time, os, struct
import logging

logger = logging.getLogger('tc-core')

def mine_block(blk: Block, verbose: bool = False) -> Block:
    '''
    Mine a block. Brute force the nonce until the hash is valid

    Args:
        blk (Block): The block to be mined

    Returns:
        Block: Reference to the block object

    '''

    mixer = os.urandom(8)

    counter = 0
    
    t0 = time.time()

    while not blk.is_hash_valid():
        blk.nonce = mixer + struct.pack('Q', counter)
        counter += 1
    
    if verbose:
        logger.debug(f'Block mined. TIME: {time.time() - t0:.3f} CYCLES: {counter}')

    return blk
