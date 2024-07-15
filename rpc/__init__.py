
import logging, time
from typing import List, Self

from coretc import Chain, Block, ChainSettings
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexdigest, data_hexundigest, dump_json, load_json_from_file
from coretc.utils.valid_data import valid_port, valid_host

from threading import Lock

from rpc.client import RPCClient

from .peers import Peer
from .settings import RPCSettings

logger = logging.getLogger('chain-rpc')

class RPC:
    def __init__(self, settings: RPCSettings):
        logger.info('Initialized RPC')
        
        self.VERSION = '0.1.0'
        self.settings = settings
        self.lock = Lock()
        self.chain: Chain = Chain(settings.get_chainsettings())
        
        self.peers: List[Peer] = []
        self.peers_in_use: List[Peer] = [] 
        
        self.rpc_client = RPCClient()

        self.load_peers()
        self.select_peers()

    def load_peers(self) -> bool:
        '''
        Load available peers from the node's peers.json file
        
        Returns:
            bool: Whether the peers where loaded successfully
        '''
        logger.debug('Loading peer information')

        peer_json = load_json_from_file(self.settings.node_directory + '/peers.json',
                                        verbose = True)

        if peer_json is None:
            logger.critical('Unable to load peers.')
            return False

        # Check if the JSON structure is valid

        if not isinstance(peer_json, list):
            logger.error('Peer info is not a list?')
            return False

        

        for peer_entry in peer_json:
            if 'host' not in peer_entry or 'port' not in peer_entry:
                logger.error('Invalid peer JSON format')
                return False
            
            host = peer_entry['host']
            port = peer_entry['port']

            if not valid_host(host) and valid_port(port):
                logger.error('Peer has invalid data')
                return False

            peerobj = Peer(host = peer_entry['host'], port = peer_entry['port'])
            
            # Check if it's a duplicate
            if peerobj in self.peers:
                logger.warn('Duplicate peer found in peers.json file!')
                continue

            # TODO: Check that the peer is not the current node,
            #       Need to check if it's an internal IP too


            self.peers.append(peerobj)

        return True
    
    def select_peers(self) -> int:
        '''
        Pings & Selects peers to use from the total peer list.

        Returns:
            int: Total peers set to be used
        '''
        
        self.peers_in_use.clear()

        for peer in self.peers:
            if self.rpc_client.ping(peer):
                self.peers_in_use.append(peer)

            if len(self.peers_in_use) >= self.settings.max_connections: break
        
        peer_count = len(self.peers_in_use)

        if peer_count == 0:
            logger.warn('No online peers found!')
        else:
            logger.debug(f'Interacting with {peer_count} other peers')

        return len(self.peers_in_use)

    def get_block(self, block_height: int) -> dict:
        '''
        Get a block's json given the height
        
        Args:
            block_height (int): Height of the target block

        Returns:
            dict: The block's JSON data in dict form
        '''

        blk = self.chain.get_block_by_height(block_height, get_top_fork = True)

        if blk is None:
            logger.warn('An invalid block height was requested')
            return {'error': 'Block not found'}

        return blk.to_json()



    def add_block(self, block_json: dict) -> dict:
        '''
        Function to submit a new block. This block will also propagate to peers if
        it's unique

        Args:
            block_json (dict): Dictionary of the block JSON, to be parsed

        Returns:
            dict: Response status of block addition
        '''
        with self.lock: 
            logger.debug('Received possible block to add')
            dump_json(block_json)

            # Validate the block's JSON format
            if not Block.valid_block_json(block_json):
                return {'status': int(BlockStatus.INVALID_ERROR)}

            # Try to add it to the RPC chain and get the result
            block: Block | None = Block.from_json(block_json)

            if block is None:
                return {'status': int(BlockStatus.INVALID_ERROR)}

            result = self.chain.add_block(block) 

            if result != BlockStatus.VALID:
                logger.warn("Block sent by peer was rejected") # TODO: Keep track of the src here too
                return {'status': int(result)}

            logger.debug('Received valid block. Added to chain.')

            # Propagate to other peers.
            logger.critical('NEW BLOCK PROPAGATION NOT IMPLEMENTED') 
        
            return {'status': int(result)}
    
    def add_tx_to_mempool(self, tx_json: dict) -> bool:
        '''
        Used to add a transaction to the node's mempool and propagate it to other nodes

        Args:
            tx_json (dict): Transaction JSON in a Dictionary
        Returns:
            bool: Whether the tx was added to the mempool
        '''
        return False

        # Check if the TX is already in the mempool

        # Try to add to the mempool

        # Share with other peers if successful

        # Return whether the tx was accepted to the caller

    def get_info(self) -> dict:
        return {
            'version': self.VERSION,
            'status': True, # TODO: Change this later to be dynamic
            'peercount': len(self.peers),
            'timestamp': int(time.time())
        }

    def get_chain_height(self) -> int:
        '''
        Returns the chain's height directly from the chain

        Returns:
            int: The height
        '''
        with self.lock:
            return self.chain.get_height()

    def get_peers_json(self) -> List[dict]:
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

    def get_top_diff(self) -> int:
        '''Get the top difficulty directly from the chain'''
        with self.lock:
            return self.chain.get_top_difficulty()
