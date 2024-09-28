
import json
from typing import Optional, Self
from dataclasses import dataclass
from enum import IntEnum

from rpc.rpcutils import NetworkType, PeerStatus, check_peer_json

# TODO: Add a penalty system at some point

@dataclass(init = True)
class Peer:
    
    host: str
    
    net: NetworkType    = NetworkType.MAINNET
    rpc_version: str    = '' # These get filled out automatically when connecting to a peer
    core_version: str   = ''

    port: int           = 1993
    
    last_height: int    = -1
    last_seen: int      = -1
    status: PeerStatus  = PeerStatus.OFFLINE

    ssl_enabled: bool   = False # TODO: Fix this at some point 

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
            'net': int(self.net),
            'version_rpc': self.rpc_version,
            'version_core': self.core_version,

            'host': self.host,
            'port': self.port,

            'last_height': self.last_height,
            'last_seen': self.last_seen,
            'last_status': int(self.status),

            'ssl_enabled': self.ssl_enabled
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
        
        if not check_peer_json(json_data): return None

        return Peer(
            net             = NetworkType(json_data['net']),
            rpc_version     = json_data['version_rpc'],
            core_version    = json_data['version_core'],

            host            = json_data['host'],
            port            = json_data['port'],

            last_height     = json_data['last_height'],
            last_seen       = json_data['last_seen'],
            status          = json_data['last_status'],

            ssl_enabled     = json_data['ssl_enabled']
        )

    def __eq__(self, other) -> bool:
        return (self.host, self.port) == (other.host, other.port)
