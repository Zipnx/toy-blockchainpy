
from typing import Iterable, List

from coretc.utils.valid_data import valid_file
from rpc.client import RPCClient
from rpc.peers import Peer, PeerStatus
import logging, json


logger = logging.getLogger('peer-manager')

class PeerManager:
    def __init__(self, rpc_client: RPCClient, peer_file: str, max_peers_used: int = 16) -> None:
        self.peer_file = peer_file
        self.rpc_client = rpc_client
        self.max_peers_used = max_peers_used
    
        if not valid_file(peer_file):
            logger.critical('Selected peer file does not exist')
        
        self.known_peers: List[Peer] = []
        self.peers_inuse: List[Peer] = []

    def load_peers(self) -> bool:
        '''
        Load the stored peer info from the peer file 
        
        Returns:
            bool: Whether the load was successful
        '''
        
        try:
            with open(self.peer_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.critical('Peer file contains invalid JSON')
            return False

        if not isinstance(data, list):
            logger.critical('Invalid peer file format!')
            return False
        
        self.known_peers.clear()

        for i, peer_json in enumerate(data):

            peer_obj: Peer | None = Peer.from_json(peer_json)

            if peer_obj is None:
                logger.warning(f'Invalid peer in peers file: #{i}')
                continue

            self.known_peers.append(peer_obj)
        
        logger.info(f'Loaded info of {len(self.known_peers)} total peers')

        return True

    def save_peers(self) -> bool:
        '''
        Load the current peer info to the peer file

        Returns:
            bool: Whether the save was successful
        '''
        
        peer_json: List[dict] = []

        for peer in self.known_peers:
            peer_json.append(peer.to_json())

        with open(self.peer_file, 'w') as f:
            json.dump(peer_json, f, indent = 4)
            f.write('\n')
        
        logger.info(f'Saved info of {len(self.known_peers)} known peers.')

        return True

    def pick_peers_used(self, max_peers_override: int | None = None) -> int:
        '''
        Pick (or re-pick) peers to actively use
        
        Args:
            max_peers_override (int | None): Used to override the peer manager's max peers in use

        Returns:
            int: Total peers selected.
        '''
        
        logger.debug('Selecting peers...')
        self.peers_inuse.clear()

        # TODO: This is the current peer selection, will shortly implement
        #       using the hellopeer functionality
        
        peer_use_count: int = 0

        for peer in self.known_peers:
            if self.rpc_client.ping(peer):

                if len(self.peers_inuse) < (self.max_peers_used if max_peers_override is None else max_peers_override):
                    self.peers_inuse.append(peer)
                    peer_use_count += 1

        if peer_use_count == 0:
            logger.warn('No online peers found!')
        else:
            logger.debug(f'Interacting with {peer_use_count} other peers.')

        return peer_use_count
    
    def add_peer_to_use(self, new_peer: Peer) -> bool:
        '''
        Add a peer to the peer_inuse list. Will return false if the peer 
        exists already in it or if adding it exceeds the max peers in use setting
        
        Returns:
            bool: Whether the addition went through
        '''

        if len(self.peers_inuse) >= self.max_peers_used: return False

        if new_peer in self.peers_inuse: return False

        if new_peer not in self.known_peers: self.known_peers.append(new_peer)

        self.peers_inuse.append(new_peer)

        return True

    def get_peers_used(self) -> Iterable[Peer]:
        '''
        Get the peers in use, in form of an Iterable

        Returns:
            Iterable[Peer]: Peers in current use
        '''

        for peer in self.peers_inuse:
            yield peer
    
    def is_peer_used(self, peer: Peer) -> bool:
        '''
        Check if a peer is being used.

        Args:
            peer (Peer): Peer to Check

        Returns:
            bool: Whether it is or not
        '''

        return peer in self.peers_inuse

    def get_peers_known(self) -> Iterable[Peer]:
        '''
        Get an iterable of all the known peers

        Returns:
            Iterable[Peer]: Peers known by the peer manager
        '''

        for peer in self.known_peers:
            yield peer
        
        
