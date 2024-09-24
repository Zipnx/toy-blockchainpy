
from os.path import exists, isdir

import os

from typing import List
from coretc.wallet import Wallet
from coretc import Chain, ChainSettings, Block, ForkBlock, TX, UTXO, difficulty, mine_block

import time

CHAIN_PATH = './pytests-chain-tmp/'

def create_empty_chain():

    chain = Chain(ChainSettings(
            debug_dont_save = True, 
            debug_log_dir = CHAIN_PATH + 'debug/',
            block_data_directory = CHAIN_PATH + 'blocks/',
            utxo_set_path = CHAIN_PATH + 'utxos.dat',
            mempool_path = CHAIN_PATH + 'mempool.dat'
        ))
    
    return chain

def create_chain_block(chain: Chain, mine: bool = True, txs: List[TX] = []) -> Block:

    blk = Block(
        previous_hash = chain.get_tophash(),
        timestamp = int(time.time()),
        difficulty_bits = chain.get_top_difficulty(),
        nonce = b'Some data',
        transactions = txs,
        _VERSION = 1
    )
    
    return blk if not mine else mine_block(blk)

def create_example_block(prev: bytes = b'\x00'*32, mine: bool = True) -> Block:
    #blk = Block(prev, 1, 0x2000FFFF, b'', [])

    blk = Block(
        previous_hash = prev,
        timestamp = int(time.time()),
        difficulty_bits = 0x2000FFFF,
        nonce = b'Some data',
        transactions = [],
        _VERSION = 1
    )

    return blk if not mine else mine_block(blk)

def create_example_tx() -> TX:
    return TX([], [])

def create_example_utxo(is_input: bool = False) -> UTXO:
    return UTXO(b'A'*91, 0.5, 0, b'i'*32, b'I am in pain')
    
def forktree_from_json(structure: list, node: ForkBlock | None = None) -> ForkBlock:

    '''
    [
        []
        [
            []
            []
        ]
    ]
    '''
    
    root = ForkBlock(None, create_example_block()) if node is None else node

    for subtree_structure in structure:
        
        root.append_block( create_example_block(prev = root.block.hash_sha256()) )
        forktree_from_json(subtree_structure, root.next[-1])

    return root


