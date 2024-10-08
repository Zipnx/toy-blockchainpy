

import logging, time
from typing import List, Literal, Tuple

from coretc.blocks import Block
from coretc.object_schemas import BLOCK_JSON_SCHEMA, is_schema_valid
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexdigest, data_hexundigest, is_valid_digit

from .peers import Peer, PeerStatus
from .rpcutils import make_rpc_request_raw

logger = logging.getLogger('chain-rpc-client')

class RPCClient:
    def __init__(self):
        self.selected_peer: Peer | None = None

    def use_peer(self, peer: Peer):
        self.selected_peer = peer
    
    def send_request(self, endpoint: str, 
                     json_data: dict | None = None,
                     method: Literal['GET', 'POST'] = 'POST',
                     peer: Peer | None = None,
                     update_peer: bool = True,
                     log_error: bool = True) -> Tuple[dict, bool]:
        
        '''
        Make a request to the selected peer (or one given manually) at a specific endpoint

        Args:
            endpoint (str): RPC Endpoint to hit, ex: /height
            json_data (dict | None): JSON Data to send, None for no data, (DEFAULT=None)
            method (Literal['GET', 'POST']): Request method (DEFAULT=POST)
            peer (Peer): Alternate peer to use instead of the selected one (DEFAULT=None)
            update_peer (bool): Whether the last_seen of the peer will be updated (DEFAULT=True)
            log_error (bool): Whether an error will be logged if encountered (DEFAULT=True)

        Returns:
            dict: Resulting JSON rpc data
            bool: Whether a request error occured
        '''
        
        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot send a request when no peer is selected')
            return ({}, True)
        
        response_json, err = make_rpc_request_raw(
            peer.form_url(endpoint),
            json_data = json_data,
            method = method
        )
        
        if err:
            if log_error:
                logger.error(f'Request error sending RPC request: {response_json["error"]}')

            return (response_json, True)
        
        if update_peer:
            peer.last_seen = int(time.time()) 

        return (response_json, False)
    
    def get_block(self, height: int, peer: Peer | None = None) -> Block | None:
        '''
        Get a block from a peer, given a height

        Args:
            height (int): Height of block to get
            peer: (Peer | None): Peer to use, else will use selected

        Returns:
            Block | None: The block object if successful, else none
        '''

        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get block from peer when none are selected')
            return None

        response_json, err = self.send_request(
            endpoint = '/getblock',
            method = 'POST',
            json_data = {
                'height': height 
            },
            peer = peer,
        )

        if err:
            logger.error(f'Network error sending get_block request to peer {peer.hoststr()}')
            return None

        if 'error' in response_json:
            logger.error(f"Peer {peer.hoststr()} returned error during get_block req: {response_json}")
            return None

        # Check the block schema
        if not Block.valid_block_json(response_json):
            logger.error(f'Peer {peer.hoststr()} send invalid block JSON for get_block req')
            return None

        blk = Block.from_json(response_json, validate_json = False) # We checked the json before 

        if blk is None:
            logger.error(f'Invalid block JSON from {peer.hoststr()}')

        return blk
    
    def get_blocks(self, height: int, count: int, peer: Peer | None = None) -> List[Block]:
        '''
        Get blocks in bulk from a peer

        Args:
            height (int): Height to get the blocks from
            count (int): How many blocks to get
            peer (Peer | None): Peer to use, else use the selected peer
        '''

        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get blocks from peer when none are selected')
            return []

        response_json, err = self.send_request(
            endpoint = '/getblocks',
            method = 'POST',
            json_data = {
                'height': height,
                'count': count
            },
            peer = peer,
        )

        if err:
            logger.error(f'Network error sending get_block request to peer {peer.hoststr()}')
            return []

        if 'error' in response_json:
            logger.error(f"Peer {peer.hoststr()} returned error during get_block req: {response_json}")
            return []

        if not is_schema_valid(response_json, {
            'type': 'array',
            'items': BLOCK_JSON_SCHEMA
        }):
            logger.error(f'Peer {peer.hoststr()} returned invalid JSON during get_blocks')
            return []

        blks: List[Block] = []

        for block_json in response_json:
            blk = Block.from_json(block_json, validate_json = False)

            if blk is None:
                logger.error(f'Peer {peer.hoststr()} returned invalid block data in JSON')
                return []

            blks.append(blk)

        return blks

    def get_tophash(self, peer: Peer | None = None) -> bytes | None:
        '''
        Get the tophash of a given peer

        Args:
            peer (Peer | None): Default is none. If none, the selected peer is used
        
        Returns:
            bytes | None: Either the tophash in byte form or None
        '''

        response_json, err = self.send_request(
            endpoint = '/tophash',
            method = 'GET',
            peer = peer
        )
         
        if err: return None

        peer = peer or self.selected_peer
        if peer is None: return None

        if 'error' in response_json:
            logger.error(f'Error getting top hash from peer {peer.hoststr()}: {str(response_json["error"])}')
            return None

        if 'tophash' not in response_json:
            logger.error(f'Peer {peer.hoststr()} gave invalid response')
            return None

        tophash = data_hexundigest(response_json['tophash'])

        if len(tophash) != 32:
            logger.error(f'Peer {peer.hoststr()} sent invalid tophash')
            return None

        return tophash
    
    def check_tophash_exists(self, hash_bytes: bytes, peer: Peer | None = None) -> bool:

        peer = peer or self.selected_peer
        
        if peer is None:
            logger.critical('Cannot check for existance of top hash if no peer is specified')
            return True
    
        response_json, err = self.send_request(
            endpoint = '/tophashexists',
            json_data = {'hash': data_hexdigest(hash_bytes)},
            method = 'POST',
            peer = peer
        )
        
        if err: return True

        if 'error' in response_json:
            logger.error(f'Error checking tophash existance from peer {peer.hoststr()}: {str(response_json)}')
            return True

        if 'exists' not in response_json:
            logger.error(f'Peer {peer.hoststr()} gave invalid response')
            return True
        
        if not isinstance(response_json['exists'], bool):
            logger.error(f'Peer {peer.hoststr()} returned invalid type for boolean')
            return True

        return response_json['exists']

    def get_topdiff(self, peer: Peer | None = None) -> int | None:
        '''
        Get the top difficulty of a given peer

        Args:
            peer (Peer | None): Default is none. If none, the selected peer is used
        Returns:
            bytes | None: Either the difficulty bits or None
        '''
        peer = peer or self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the top difficulty when no peer is specified')
            return None

        response_json, err = self.send_request(
            endpoint = '/topdifficulty',
            json_data = None,
            method = 'GET',
            peer = peer
        )



        if 'error' in response_json:
            logger.error(f'Error getting top difficulty from peer {peer.hoststr()}: {str(response_json["error"])}')
            return None

        if 'difficulty' not in response_json:
            logger.error(f'Peer {peer.hoststr()} gave invalid response')
            return None

        if not isinstance(response_json['difficulty'], int):
            if not str(response_json['difficulty']).isdigit(): 
                logger.error(f'Invalid difficulty data sent by {peer.hoststr()}')
                return None

        diff = int(response_json['difficulty'])

        if diff.bit_length() > 30 or diff <= 0:
            logger.error(f'Peer {peer.hoststr()} sent invalid top difficulty')
            return None

        return diff
    
    def get_height(self, peer: Peer | None = None) -> int:
        '''
        Get the height of a peer node

        Returns:
            int: The height. Will be <0 in case of an error
        '''
        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get height from unspecified peer')
            return -1

        response_json, err = self.send_request(
            endpoint = '/height',
            json_data = None,
            method = 'GET',
            peer = peer
        )
        
        if err: return -1

        if 'error' in response_json:
            logger.error(f'Error getting height from {peer.hoststr()}: {response_json["error"]}')

        if 'height' not in response_json:
            logger.error(f'Height req to {peer.hoststr()} returned invalid response')
            return -1

        if not is_valid_digit(response_json['height']):
            logger.error(f'Height req to {peer.hoststr()} returned NaN')
            return -1

        return int(response_json['height'])
    
    def get_estab_height(self, peer: Peer | None = None) -> int:
        '''
        Get the established height of a peer node

        Returns:
            int: The height, <0 on error
        '''
        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('A peer must be selected to get the estab height')
            return -1

        response_json, err = self.send_request(
            endpoint    = '/estabheight',
            method      = 'GET',
            peer        = peer
        )

        if err: return -1
        
        if 'error' in response_json:
            logger.error(f'Established height req to {peer.hoststr()} returned error: {response_json["error"]}')
            return -1

        if 'height' not in response_json:
            logger.error(f'Established height req to {peer.hoststr()} returned invalid response')
            return -1

        if not is_valid_digit(response_json['height']):
            logger.error(f'Established height req to {peer.hoststr()} returned NaN')
            return -1

        return int(response_json['height'])

    def submit_block(self, block: Block, peer: Peer | None = None) -> BlockStatus:
        '''
        Submit a block to another node.

        Args:
            block (Block): Block to share
            peer (Peer | None): Default is None. If none use the selected peer
        Returns:
            BlockStatus: The addition response status from the other peer
        '''
        
        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return BlockStatus.INVALID_ERROR

        response_json, err = self.send_request(
            endpoint = '/submitblock',
            json_data = block.to_json(),
            method = 'POST',
            peer = peer
        ) 
       
        if err: return BlockStatus.INVALID_ERROR

        if 'error' in response_json:
            logger.error(f'Error accessing {peer.hoststr()}: {response_json["error"]}')

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
    
    def get_foreign_peers(self, peer: Peer | None = None) -> dict:
        '''
        Get the peer list of a foreign node

        Args:
            peer (Peer | None): Optionally a specific peer to ping
        Returns:
            dict: Peer information separated by all and currently active peers
        '''
        result: dict = {
            'banned': [],
            'limited': [],
            'offline': [],
            'online': [],
            'used': []
        }
        
        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get peer information when no peer is specified')
            return result
        
        response_json, err = self.send_request(
            endpoint = '/peers', 
            json_data = None,
            method = 'GET',
            peer = peer
        )
        
        if err: return result

        if 'error' in response_json:
            logger.error(f'Error getting peer list of {peer.hoststr()}: {response_json["error"]}')
            return result

        fields = ['banned', 'limited', 'offline', 'online', 'used']

        for f in fields:
            if f not in response_json:
                logger.error(f'Peer {peer.hoststr()} sent invalid peer list response')
                continue
        
            if not isinstance(response_json[f], list):
                logger.error(f'Peer {peer.hoststr()} sent invalid peer list response (not list)')
                continue

            for peer_json in response_json[f]:
                peer_obj = Peer.from_json(peer_json)

                if peer_obj is None:
                    logger.error(f'Peer list response from {peer.hoststr()} contained invalid peer JSON')
                    continue

                result[f].append(peer_obj)

        return result
     
    def ping(self, peer: Peer | None = None) -> bool:
        '''
        Peer the currently selected Peer, or one specified

        Args:
            peer (Peer | None): Optionally a specific peer to ping
        Returns:
            bool: Whether the ping was successful
        '''

        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return False
        
        peer.status = PeerStatus.OFFLINE

        response_json, err = make_rpc_request_raw(
            peer.form_url('/ping'),
            json_data = None,
            method = 'POST'
        )
        
        #print(response_json)

        if 'error' in response_json or err:
            return False

        if 'msg' not in response_json and 'stamp' not in response_json:
            logger.warning(f'Peer {peer.hoststr()} sent invalid ping response')
            return False

        # TODO: Also do something with the returned timestamp idk

        if str(response_json['msg']) != 'pong': return False

        peer.status = PeerStatus.ONLINE
        peer.last_seen = int(time.time())

        return True


