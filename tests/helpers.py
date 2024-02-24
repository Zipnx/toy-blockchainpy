
from coretc import Block, TX, UTXO

def create_example_block() -> Block:
    return Block(b'\x00'*32, 1, 0x2000FFFF, b'', [])

def create_example_tx() -> TX:
    return TX([], [])

def create_example_utxo() -> UTXO:
    return UTXO(b'A'*32, 0.5, b'B'*32, 0, b'')
