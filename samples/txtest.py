
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json

from coretc import Chain, Block, TX, UTXO, BlockStatus, mine_block

def main():

    idk: TX = TX([], [], b'', b'')
    
    idk.inputs.append(UTXO(
        b'A'*32,
        0.5,
        0
    ))

    idk.gen_txid()
    idk.gen_nonce()

    print(json.dumps(idk.to_json(), indent = 4))


if __name__ == '__main__':
    main()
