
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from binascii import hexlify

import time, json

from coretc import Chain, Block, TX, UTXO, BlockStatus, mine_block

def main():
    return
    

if __name__ == '__main__':
    main()
