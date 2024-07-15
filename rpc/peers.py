
from typing import Optional, Self
from dataclasses import dataclass
from enum import IntEnum

class PeerStatus(IntEnum):
    OFFLINE = 0
    ONLINE  = 1
    LIMITED = 2
    BANNED  = 3

# TODO: Add a penalty system at some point

@dataclass(init = True)
class Peer:
    host: str
    port: int = 1993
    
    status: PeerStatus = PeerStatus.OFFLINE

    ssl_enabled: bool = False # TODO: Fix this at some point 

    def form_url(self, endpoint: str = '/') -> str:
        '''
        Get the rpc endpoint url of the peer. Can also specify which endpoint

        Args:
            endpoint (str): RPC Endpoint, by default /
        Returns:
            str: Resulting RPC url
        '''
        if len(endpoint) <= 0: endpoint = '/'

        if not endpoint[0] == '/': endpoint = '/' + endpoint

        return f'{"https" if self.ssl_enabled else "http"}://{self.host}:{self.port}{endpoint}'
    
    def hoststr(self) -> str:
        '''
        Get the host string. Which is the host and port in format IP:PORT

        Returns:
            str: Said host string
        '''
        return f'{self.host}:{self.port}'

    def to_json(self) -> dict:
        '''
        Convert the Peer into a JSON object

        Returns:
            dict: Resulting dict
        '''
        return {
            'host': self.host,
            'port': self.port
        }

    @staticmethod
    def from_json(json_data: dict) -> Optional['Peer']:
        '''
        Form a peer object given JSON data

        Args:
            json_data (dict): Peer data in JSON format
        Returns:
            Peer | None: The resulting Peer object or None if an error occured
        '''
        params = ['host', 'port']

        for param in params:
            if param not in json_data:
                return None
        
        if not isinstance(json_data['port'], int):
            if not str(json_data['port']).isdigit(): return None

        return Peer(
            host = json_data['host'],
            port = int(json_data['port'])
        )

    def __eq__(self, other) -> bool:
        return (self.host, self.port) == (other.host, other.port)
