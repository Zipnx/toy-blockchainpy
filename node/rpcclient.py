

import logging, requests
from coretc.blocks import Block
from coretc.status import BlockStatus
from node.peers import Peer

logger = logging.getLogger('chain-rpc-client')

class RPCClient:
    def __init__(self):
        self.selected_peer: Peer | None = None

    def use_peer(self, peer: Peer):
        self.selected_peer = peer

    def submit_block(self, block: Block, peer: Peer | None = None) -> BlockStatus:
        '''
        Submit a block to another node.

        Args:
            block (Block): Block to share
            peer (Peer | None): Default is None. If none use the selected peer
        Returns:
            BlockStatus: The addition response status from the other peer
        '''
        
        if peer is None and self.selected_peer is None:
            logger.critical('Attempted to send data to peer with no peer selected')
            return BlockStatus.INVALID_ERROR

        if peer is None: peer = self.selected_peer
        
        r = requests.post(peer.form_url('/submitblock'), json = block.to_json())
        
        response_json = r.json()

        if 'status' not in response_json:
            logger.error('Invalid response from peer where block was submitted')
            return BlockStatus.INVALID_ERROR

        status = response_json['status']

        if not isinstance(status, int):
            if not str(status).isdigit(): 
                logger.error('Invalid status code from peer where block was submitted')
                return BlockStatus.INVALID_ERROR
            
            status = int(status)

        try:
            blockstatus = BlockStatus(status)
        except ValueError:
            logger.error(f'Unknown status code returned by foreign peer: {status}')
            return BlockStatus.INVALID_ERROR

        return blockstatus
