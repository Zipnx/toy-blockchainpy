

import logging, requests
from typing import List

from coretc.blocks import Block
from coretc.status import BlockStatus
from coretc.utils.generic import data_hexundigest

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

        if peer is None:
            peer = self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return None

        response_json = make_rpc_request(
            peer.form_url('/tophash'),
            json_data = None,
            method = 'GET'
        )

        if response_json is None:
            response_json = {'error': 'Request error when accessing peer'}

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
    
    def get_topdiff(self, peer: Peer | None = None) -> int | None:
        '''
        Get the top difficulty of a given peer

        Args:
            peer (Peer | None): Default is none. If none, the selected peer is used
        Returns:
            bytes | None: Either the difficulty bits or None
        '''

        if peer is None:
            peer = self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the top difficulty when no peer is specified')
            return None

        response_json = make_rpc_request(
            peer.form_url('/topdifficulty'),
            json_data = None,
            method = 'GET'
        )

        if response_json is None:
            response_json = {'error': 'Request error when accessing peer'}
        
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

    def submit_block(self, block: Block, peer: Peer | None = None) -> BlockStatus:
        '''
        Submit a block to another node.

        Args:
            block (Block): Block to share
            peer (Peer | None): Default is None. If none use the selected peer
        Returns:
            BlockStatus: The addition response status from the other peer
        '''
        
        if peer is None:
            peer = self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return BlockStatus.INVALID_ERROR

        response_json = make_rpc_request(
            peer.form_url('/submitblock'),
            json_data = block.to_json(),
            method = 'POST'
        ) 
        
        if response_json is None:
            logger.error(f'Unable to access peer {peer.hoststr()} to send block JSON')
            return BlockStatus.INVALID_ERROR

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
        
        if peer is None:
            peer = self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get peer information when no peer is specified')
            return result
        
        response_json = make_rpc_request(
            peer.form_url('/peers'), 
            json_data = None,
            method = 'GET'
        )

        if response_json is None:
            logger.error(f'Unable to get peer list of {peer.hoststr()}')
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

    def ping(self, peer: Peer | None) -> bool:
        '''
        Peer the currently selected Peer, or one specified

        Args:
            peer (Peer | None): Optionally a specific peer to ping
        Returns:
            bool: Whether the ping was successful
        '''

        if peer is None:
            peer = self.selected_peer
        
        if peer is None:
            logger.critical('Cannot get the tophash when no peer is specified')
            return False
        
        peer.status = PeerStatus.OFFLINE

        response_json = make_rpc_request(
            peer.form_url('/ping'),
            json_data = None,
            method = 'POST'
        )
        
        if response_json is None:
            return False

        if 'msg' not in response_json and 'stamp' not in response_json:
            logger.warn(f'Peer {peer.hoststr()} sent invalid ping response')
            return False

        # TODO: Also do something with the returned timestamp idk

        if str(response_json['msg']) != 'pong': return False

        peer.status = PeerStatus.ONLINE

        return True


