
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from binascii import hexlify

import time, json

from coretc import Chain, Block, TX, UTXO, BlockStatus, mine_block

def main():
    
    idk: TX = TX([], [], b'some nonce')

    idk.inputs.append(UTXO(
        b'A'*32,
        0.69,
        0
    ))

    idk.gen_txid()
    
    idk_json = idk.to_json()
    print(json.dumps(idk_json, indent = 4))
    print(f'Original TXID: {idk_json["txid"]}\n')

    txcopy: TX = TX.from_json(idk_json)
    txcopy.gen_txid()

    copy_json = txcopy.to_json()
    print(json.dumps(copy_json, indent = 4))
    print(f'Copy TXID: {copy_json["txid"]}')
    

    return

    chain: Chain = Chain()


    blk = Block(chain.get_tophash(), int(time.time()), chain.get_current_difficulty(), b'', [])
    mine_block(blk)

    json_data = blk.to_json()
    print(json.dumps(json_data, indent = 4))
    print(f'Block hash: {json_data["hash"]}\n')

    blk_copy: Block = Block.from_json(json_data)
    
    copy_data = blk_copy.to_json()
    print(json.dumps(copy_data, indent = 4))
    print(f'Copy block hash: {copy_data["hash"]}')


    #mine_block(blk)
        

    

if __name__ == '__main__':
    main()
