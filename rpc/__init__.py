
import logging, time
from typing import List, MutableMapping, Tuple

from coretc import Chain, Block, ChainSettings
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexdigest, data_hexundigest, dump_json, load_json_from_file
from coretc.utils.valid_data import valid_port, valid_host

from threading import Lock

from rpc.client import RPCClient

from rpc.peer_manager import PeerManager
from rpc.peers import Peer, PeerStatus, get_peer_list_json
from rpc.rpcutils import NetworkType
from rpc.settings import RPCSettings

logger = logging.getLogger('chain-rpc')

class RPC:
    def __init__(self, settings: RPCSettings):
        logger.info('Initialized RPC')
        
        self.VERSION = '0.2.0'
        self.settings = settings
        self.lock = Lock()
        self.chain: Chain = Chain(settings.get_chainsettings())
        
        #self.peers: List[Peer] = []
        #self.peers_in_use: List[Peer] = [] 
        
        self.rpc_client = RPCClient()

        self.peer_manager = PeerManager(
            rpc_client      = self.rpc_client,
            peer_file       = self.settings.node_directory + '/peers.json',
            max_peers_used  = self.settings.max_connections
        )

        self.peer_manager.load_peers()
        self.peer_manager.pick_peers_used(self.get_info_ext())
 
    def handle_hello(self, host_ip: str, ext_peer_info: dict) -> dict:
        '''
        Handle a hello request and if valid add the peer to the current peers
        *** THE NODE INFO IS NOT VALIDATED HERE ***

        Args:
            host_ip (str): IP (or dns im dumb) of foreign peer
            ext_peer_info (dict): The other peer's extended node info

        Returns:
            dict: RPC Response
        '''

        with self.lock:

            # TODO: Also validate the network type
            
            if self.peer_manager.is_use_limit_reached():
                return {
                    'info': {},
                    'success': False
                }

            new_peer = Peer(
                net = NetworkType(ext_peer_info['net']),
                
                rpc_version = ext_peer_info['version_rpc'],
                core_version = ext_peer_info['version_core'],

                host = host_ip,
                port = ext_peer_info['port'],
                last_seen = int(time.time()),
                last_height = ext_peer_info['height'],
                status = PeerStatus.ONLINE,
                ssl_enabled = ext_peer_info['ssl']
            )

            # TODO: Challenge the peer, make sure the chains are compatible, net, versions, etc
            # TODO: If the height is higher than this nodes, check for sync

            # Does not work when the peer boots, will fix later
            #if not self.rpc_client.ping(new_peer):
            #    return {'error': 'Did not respond to ping'}

            self.peer_manager.add_peer_to_use(new_peer)
        
            logger.debug(f'New peer found: {new_peer.hoststr()}')


            logger.debug(f'Interacting with {len(self.peer_manager.peers_inuse)} other peers')

            return {
                'info': self.get_info_ext(), 
                'success': True
            }

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
        
        for peer in self.peer_manager.get_peers_used():
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

        for peer in self.peer_manager.get_peers_used():
            
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
            'net': NetworkType.MAINNET,  # Change later in the node setup
            'ssl': self.settings.ssl_enabled,
            'version_rpc': self.VERSION,
            'version_core': '1.2.3', # TODO: This is all wrong, needs to be of type int
            'height': self.chain.get_height(),
            'peercount': len(self.peer_manager.known_peers),
            'timestamp': int(time.time())
        }
    
    # Benchmark how heavy this is
    def get_info_ext(self) -> dict:
        node_info = self.get_info()

        extended = {
            'port': self.settings.port,
            'estabheight': self.chain.get_established_height(),
            'tophash': data_hexdigest(self.chain.get_tophash()),
            'peers': get_peer_list_json(self.peer_manager.get_peers_known()),
            'peers_used': get_peer_list_json(self.peer_manager.get_peers_used())
        }

        return {**node_info, **extended}

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
            print(len(list(self.peer_manager.get_peers_known()))) 
            for peer in self.peer_manager.get_peers_known():
                print(peer)
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

                if self.peer_manager.is_peer_used(peer):
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
