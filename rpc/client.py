

import logging, requests
from typing import List

from coretc.blocks import Block
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexdigest, data_hexundigest, is_valid_digit

from .peers import Peer, PeerStatus
from .rpcutils import make_rpc_request

logger = logging.getLogger('chain-rpc-client')

class RPCClient:
    def __init__(self):
        self.selected_peer: Peer | None = None

    def use_peer(self, peer: Peer):
        self.selected_peer = peer
    

    def get_tophash(self, peer: Peer | None = None) -> bytes | None:
        '''
        Get the tophash of a given peer

        Args:
            peer (Peer | None): Default is none. If none, the selected peer is used
        Returns:
            bytes | None: Either the tophash in byte form or None
        '''
        peer = peer or self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return None

        response_json = make_rpc_request(
            peer.form_url('/tophash'),
            json_data = None,
            method = 'GET'
        )

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
    
    def check_tophash_exists(self, hash_bytes: bytes, peer: Peer | None) -> bool:

        peer = peer or self.selected_peer
        
        if peer is None:
            logger.critical('Cannot check for existance of top hash if no peer is specified')
            return True
    
        response_json = make_rpc_request(
            peer.form_url('/tophashexists'),
            json_data = {'hash': data_hexdigest(hash_bytes)},
            method = 'POST'
        )

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

        response_json = make_rpc_request(
            peer.form_url('/topdifficulty'),
            json_data = None,
            method = 'GET'
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

        response_json = make_rpc_request(
            peer.form_url('/height'),
            json_data = None,
            method = 'POST'
        )
        
        if 'error' in response_json:
            logger.error(f'Error getting height from {peer.hoststr()}: {response_json["error"]}')

        if 'height' not in response_json:
            logger.error(f'Height req to {peer.hoststr()} returned invalid response')
            return -1

        if not is_valid_digit(response_json['height']):
            logger.error(f'Height req to {peer.hoststr()} returned NaN')
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

        response_json = make_rpc_request(
            peer.form_url('/submitblock'),
            json_data = block.to_json(),
            method = 'POST'
        ) 
        
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
        
        response_json = make_rpc_request(
            peer.form_url('/peers'), 
            json_data = None,
            method = 'GET'
        )

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
    
    def peer_establish(self, node_info: dict, peer: Peer | None) -> bool:
        '''
        Send the node information to a foreign peer to establish a connection

        Args:
            node_info (dict): Node information in JSON format

        Returns:
            bool: Whether the data was accepted.
        '''

        peer = peer or self.selected_peer

        if peer is None:
            logger.critical('Cannot establish connection with an unspecified peer')
            return False

        response_json = make_rpc_request(
            peer.form_url('/hellopeer'),
            json_data = node_info,
            method = 'POST'
        )

        if 'error' in response_json:
            logger.error(f'Error sending hello to {peer.hoststr()}: {response_json}')
            return False

        if 'status' not in response_json:
            logger.error(f'Peer {peer.hoststr()} sent invalid hello response')
            return False

        if not isinstance(response_json['status'], bool):
            logger.error(f'Peer {peer.hoststr()} sent invalid hello response type')
            return False

        return response_json['status']

    def ping(self, peer: Peer | None) -> bool:
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

        response_json = make_rpc_request(
            peer.form_url('/ping'),
            json_data = None,
            method = 'POST'
        )
        
        if 'error' in response_json:
            return False

        if 'msg' not in response_json and 'stamp' not in response_json:
            logger.warn(f'Peer {peer.hoststr()} sent invalid ping response')
            return False

        # TODO: Also do something with the returned timestamp idk

        if str(response_json['msg']) != 'pong': return False

        peer.status = PeerStatus.ONLINE

        return True


