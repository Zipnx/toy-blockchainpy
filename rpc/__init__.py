
import logging, time
from typing import List, MutableMapping, Self, Tuple

from coretc import Chain, Block, ChainSettings
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexdigest, data_hexundigest, dump_json, load_json_from_file
from coretc.utils.valid_data import valid_port, valid_host

from threading import Lock

from rpc.client import RPCClient

from .peers import Peer, PeerStatus
from .settings import RPCSettings

logger = logging.getLogger('chain-rpc')

class RPC:
    def __init__(self, settings: RPCSettings):
        logger.info('Initialized RPC')
        
        self.VERSION = '0.2.0'
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
        
        # This might be inefficient if a lot of peers are in the known list but it's a problem
        # ill fix some other time. I find it better to know the status of all known peers
        for peer in self.peers:
            if self.rpc_client.ping(peer):
                
                if len(self.peers_in_use) < self.settings.max_connections:
                    self.peers_in_use.append(peer)
        
        peer_count = len(self.peers_in_use)

        if peer_count == 0:
            logger.warn('No online peers found!')
        else:
            logger.debug(f'Interacting with {peer_count} other peers')

        return len(self.peers_in_use)
    
    def sync_height(self) -> int:
        '''
        Check the used nodes and sync with the top one
        
        Returns:
            int: Height synced to
        '''
         
        # Gotta think about malicious nodes that send a fake height response & how to handle that
        # My idea rn is to temporarily store those blocks in a list, since they may have to be reverted
        
        # First lets get the heights of all our peers and sort them descending
        peer_heights: MutableMapping[Peer, int] = {}
        
        for peer in self.peers_in_use:
            peer_height = self.rpc_client.get_height(peer)

            if peer_height > self.chain.get_height():
                peer_heights[peer] = peer_height
        
        if len(peer_heights) == 0:
            logger.info('No need to sync. Chain up to date.')
            return self.chain.get_height()

        # Need to be able to give a node our latest hash and get the number of additional blocks it has

        return -1

    def get_block(self, block_height: int) -> dict:
        '''
        Get a block's json given the height
        
        Args:
            block_height (int): Height of the target block

        Returns:
            dict: The block's JSON data in dict form
        '''
        
        with self.lock:
            blk = self.chain.get_block_by_height(block_height, get_top_fork = True)

            if blk is None:
                logger.warn('An invalid block height was requested')
                return {'error': 'Block not found'}

            return blk.to_json()

    def get_blocks(self, block_height: int, block_count: int) -> list:
        '''
        Get blocks in bulk
        *** THIS WILL BE CHANGED, MAYBE BSON OR SMTH IDK ***

        Args:
            block_height (int): Height from which the blocks will come after (inclusive)
            block_count  (int): Count of blocks returned

        Returns:
            dict: The blocks' JSON data in dict form
        '''
        
        # TODO: Make an actual bulk retrieval, this is dogshit for perf
        
        with self.lock:
            blocks: List[dict] = []

            for height in range(block_height, min(block_height + block_count, self.chain.get_height())):
                blk = self.get_block(height)

                if 'error' in blk: return blk

                blocks.append(blk)

            return blocks

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
            prop_count, prop_err_count = self.propagate_block(block)
        
            logger.info(f'Block propagated to {prop_count} peers. Rejected by {prop_err_count} peers')

            return {'status': int(result)}
    
    def propagate_block(self, block: Block) -> Tuple[int, int]:
        '''
        Propagate the block to peers

        Args:
            block (Block): Block to propagate

        Returns:
            Tuple[int, int]: The number of peers to which the block was passed and number rejected
        '''

        #logger.critical('NEW BLOCK PROPAGATION NOT IMPLEMENTED') 
        
        blockhash = block.hash_sha256()

        # For all peers in use, check if the block is in their chain, if not send it
        sent_block_count: int = 0
        rej_block_count: int  = 0

        for peer in self.peers_in_use:
            
            if self.rpc_client.check_tophash_exists(blockhash, peer): continue
            
            sent_block_count += 1

            if not self.rpc_client.submit_block(block, peer) == BlockStatus.VALID:
                rej_block_count += 1
                logger.warn(f'Peer {peer.hoststr()} rejected propagated block. Why?')

        return sent_block_count, rej_block_count

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

    def get_peers_json(self) -> dict:
        '''
        Retrieve a list of peer information to share

        Returns:
            dict: Peer info, separated by all and active peers
        '''

        with self.lock:
            result = {
                'offline': [],
                'online': [],
                'limited': [],
                'banned': [],
                'used': []
            }
            
            for peer in self.peers:

                peer_json = peer.to_json()

                match peer.status:
                    case PeerStatus.OFFLINE:
                        result['offline'].append(peer_json)
                    case PeerStatus.ONLINE:
                        result['online'].append(peer_json)
                    case PeerStatus.LIMITED:
                        result['limited'].append(peer_json)
                    case PeerStatus.BANNED:
                        result['banned'].append(peer_json)

                if peer in self.peers_in_use:
                    result['used'].append(peer_json)

            return result
    
    def check_tophash_exists(self, blockhash: bytes) -> dict:
        return {'exists': self.chain.check_tophash_exists(blockhash)}

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
