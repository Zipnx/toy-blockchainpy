
# Add the ../ directory to PATH to be able to use coretc
import os,sys,time, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc.settings import ChainSettings

from coretc import Chain, Block, mine_block
from rpc.client import RPCClient
from rpc.peers import Peer

urllib_log = logging.getLogger('urllib3.connectionpool')
urllib_log.disabled = True

def sample_block(bc: Chain, prev: bytes = b'') -> Block:
    if prev:
        blk = Block(prev, int(time.time()), bc.get_top_difficulty(), b'', [])
    else:
        blk = Block(bc.get_tophash(), int(time.time()), bc.get_top_difficulty(), b'', [])
    mine_block(blk, True)
    return blk

def main():

    rpc = RPCClient()
    rpc.use_peer(Peer('127.0.0.1', 2000))
    #rpc.use_peer(Peer('127.0.0.1', 2001))
    #rpc.use_peer(Peer('127.0.0.1', 2002))
    
    print(rpc.get_tophash())
    print(rpc.get_topdiff())

    #return

    chain = Chain(ChainSettings(debug_dont_save=True))

    for i in range(16):
        if i == 7:
            block = sample_block(chain, prev = b'\x69'*32)

        else:
            block = sample_block(chain)
        chain.add_block(block)
        rpc.submit_block(block)

if __name__ == '__main__':
    main()
