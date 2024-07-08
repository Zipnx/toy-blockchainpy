
import logging
from typing import List

from coretc import Chain, Block, ChainSettings
from coretc.utils.generic import data_hexdigest, data_hexundigest

from threading import Lock

from node.peers import Peer

logger = logging.getLogger('chain-rpc')

class RPC:
    def __init__(self):
        logger.info('Initialized RPC')
        
        self.lock = Lock()
        self.chain: Chain = Chain(ChainSettings())
        self.peers: List[Peer] = []

    def get_chain_height(self) -> int:
        '''
        Returns the chain's height directly from the chain

        Returns:
            int: The height
        '''
        with self.lock:
            return self.chain.get_height()

    def get_peer_list(self) -> List[dict]:
        '''
        Retrieve a list of peer information to share

        Returns:
            dict: Peer info
        '''

        with self.lock:
            output = []
        
            for peer in self.peers:
                output.append(peer.to_json())

            return output

    def get_top_hash(self) -> str:
        '''
        Retrieve the current top hash in the chain of this node

        Returns:
            str: String format of the hash
        '''

        with self.lock:
            return data_hexdigest(self.chain.get_tophash(), no_prefix = True)
