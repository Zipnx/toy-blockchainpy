
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from binascii import hexlify

import time, json

from coretc import Chain, Block, TX, UTXO, BlockStatus, mine_block

def main():

    idk: TX = TX([], [], b'', b'')
    
    idk.inputs.append(UTXO(
        b'\xAA'*32,
        0.69,
        b'\x00'*32,
        0,
        b'some shit'
    ))

    idk.set_txid()

    print(json.dumps(idk.to_json(), indent = 4))


if __name__ == '__main__':
    main()
