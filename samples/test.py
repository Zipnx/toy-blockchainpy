
#!/usr/bin/env python3

from typing import List

# Done to import the core package
import time, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.blocks import Block

from binascii import hexlify

chain: List[Block] = []

def new_testblock(nonce: bytes = b'') -> Block:

    newBlock: Block = Block(
        previous_hash = chain[-1].hash_sha256() if len(chain) > 0 else b'\x00' * 32,
        timestamp = int(time.time()),
        difficulty_bits = 0,
        nonce = nonce,
        transactions = []
    )

    return newBlock


def main():
    
    for i in range(8):
        print(f'{"="*5} New Block #{i} {"="*5}')
        chain.append(new_testblock())
        print(chain[-1])
        print(f'Hash: 0x{hexlify(chain[-1].hash_sha256()).decode()}')
    

if __name__ == '__main__':
    main()
