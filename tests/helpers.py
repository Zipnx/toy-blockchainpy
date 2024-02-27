
from coretc import Block, ForkBlock, TX, UTXO, mine_block

def create_example_block(prev: bytes = b'\x00'*32) -> Block:
    return mine_block(Block(prev, 1, 0x2000FFFF, b'', []))

def create_example_tx() -> TX:
    return TX([], [])

def create_example_utxo() -> UTXO:
    return UTXO(b'A'*32, 0.5, 0)


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


