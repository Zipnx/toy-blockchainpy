
#!/usr/bin/env python3

from typing import List

# Done to import the core package
import time, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.blocks import Block
from core.miner import mine_block

from binascii import hexlify

chain: List[Block] = []

def new_testblock(nonce: bytes = b'') -> Block:

    newBlock: Block = Block(
        previous_hash = chain[-1].hash_sha256() if len(chain) > 0 else b'\x00' * 32,
        timestamp = int(time.time()),
        difficulty_bits = 0x2000FFFF, # 256 Hash calculations on average
        nonce = nonce,
        transactions = []
    )

    return newBlock

def add_block(reqBlock: Block) -> bool:

    if not reqBlock.previous_hash == (chain[-1].hash_sha256() if len(chain) > 0 else b'\x00'*32):
        return False
    
    if not reqBlock.is_hash_valid():
        return False

    chain.append(reqBlock)
    return True


def main():
    
    for i in range(8):
        print(f'{"="*5} New Block #{i} LEN=({len(chain)}) {"="*5}')
            
        newblk = new_testblock()
        
        mine_block(newblk) 

        if add_block(newblk):
            print(f'Block accepted {str(newblk)}')

        else:
            print('Block rejected')


    

if __name__ == '__main__':
    main()
