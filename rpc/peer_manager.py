
from typing import Iterable, List

from rpc.peers import Peer, PeerStatus
import logging


logger = logging.getLogger('peer-manager')

class PeerManager:
    def __init__(self, peer_file: str) -> None:
        self.peer_file = peer_file
    
    def load_peers(self) -> bool:
        '''
        Load the stored peer info from the peer file 
        
        Returns:
            bool: Whether the load was successful
        '''
        logger.critical('UNIMPLEMENTED')
        
        return False

    def save_peers(self) -> bool:
        '''
        Load the current peer info to the peer file

        Returns:
            bool: Whether the save was successful
        '''
        logger.critical('UNIMPLEMENTED')

        return False

    def pick_peers_used(self) -> int:
        '''
        Pick (or re-pick) peers to actively use
        
        Returns:
            int: Total peers selected.
        '''
        
        logger.critical('UNIMPLEMENTED')
        return -1

    def get_peers_used(self) -> Iterable[Peer]:
        '''
        Get the peers in use, in form of an Iterable

        Returns:
            Iterable[Peer]: Peers in current use
        '''

        logger.critical('UNIMPLEMENTED')
        return []
