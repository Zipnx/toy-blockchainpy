
import logging
import requests

from enum import IntEnum
from typing import Literal, Tuple

from coretc.utils.valid_data import valid_host, valid_port, valid_version

from dataclasses import dataclass
from jsonschema import ValidationError
from jsonschema import validate as validate_schema

logger = logging.getLogger('chain-rpc')

class NetworkType(IntEnum):
    MAINNET = 0
    TESTNET = 1

class PeerStatus(IntEnum):
    OFFLINE = 0
    ONLINE  = 1
    LIMITED = 2
    BANNED  = 3

def make_rpc_request_raw(url: str, json_data: dict | None = None, method: Literal['POST', 'GET'] = 'POST') -> Tuple[dict, bool]:
    '''
    Make an RPC request to a Peer and return any returned JSON data

    Args:
        url (str): Peer RPC endpoint to access
        json_data (dict | None): JSON data to send (DEFAULT=None)
        method: Literal['post', 'get']: HTTP Method to use, default is POST
    Returns:
        dict: JSON response data if it exists. If an error occurs it will be present under the key 'error' in the dict.
    '''

    try:
        r = requests.request(method, url, json = json_data)
    except requests.exceptions.ConnectionError:
        return ({'error': f'Unable to connect to {url}'}, True)
    except BaseException as e:
        logger.error(f'Exception when attempting to access {url}: {str(e)}')
        return ({'error': f'Exception while accessing {url}: {str(e)}'}, True)
    
    if r.status_code != 200:
        logger.warning(f'Got status code: {r.status_code}, when accessing {url}')
        return ({'error': f'Invalid status code accessing {url}: {r.status_code}'}, True)

    return r.json(), False

NET_TYPE_LST = list(NetworkType)
PEER_STATUS_LIST = list(PeerStatus)

PEER_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        
        'net': {'type': 'number', 
                'minimum': int(min(NET_TYPE_LST)), 'maximum': int(max(NET_TYPE_LST))},

        'version_rpc': {'type': 'string'}, # TODO: Add network format tests 
        'version_core': {'type': 'string'},

        'host': {'type': 'string'},
        'port': {'type': 'integer', 'minimum': 0, 'maximum': 65535},

        'last_height': {'type': 'integer', 'minimum': -1},
        'last_seen': {'type': 'integer', 'minimum': -1},
        'last_status': {'type': 'number',
                        'minimum': int(min(PEER_STATUS_LIST)), 'maximum': int(max(PEER_STATUS_LIST))},
        
        'ssl_enabled': {'type': 'boolean'}

    },
    'required': [
        'net', 'version_rpc', 'version_core',
        'host', 'port',
        'last_height', 'last_seen', 'last_status',
        'ssl_enabled'
    ]
}

NODE_INFO_SHEMA = {
    'type': 'object',
    'properties': {
        
        'net': {'type': 'number'},
        'ssl': {'type': 'boolean'},
        'version_rpc': {'type': 'string'},
        'version_core': {'type': 'string'},
        'height': {'type': 'integer', 'minimum': 0},
        'peercount': {'type': 'integer', 'minimum': 0},
        'timestamp': {'type': 'integer', 'minimum': 0}
    },
    'required': [
        'net', 'ssl',
        'version_rpc', 'version_core',
        'height',
        'peercount',
        'timestamp'
    ]
}

NODE_INFO_EXT_SCHEMA = {
    
    'allOf': [

        NODE_INFO_SHEMA,
        {
            'type': 'object',
            'properties': {
        
                'port': {'type': 'integer'},

                'estabheight': {'type': 'integer', 'minimum': 0},
                'tophash': {'type': 'string'}, # TODO: Add the hash hexlify pattern check here
                'peers': {
                    'type': 'array',
                    'items': PEER_JSON_SCHEMA
                },
                'peers_used': {
                    'type': 'array',
                    'items': PEER_JSON_SCHEMA
                }
            },
            'required': [
                'port',
                'estabheight',
                'tophash',
                'peers', 'peers_used'
            ]
        }
    ]
}

def check_peer_json(json_data: dict) -> bool:
    '''
    Check if a given json dict is valid for the peer json schema

    Args:
        json_data (dict): Given JSON peer data

    Returns:
        bool: Whether it's valid
    '''
    

    # Initial validation of the schema
    try:
        validate_schema(json_data, schema = PEER_JSON_SCHEMA)
    except ValidationError:
        return False

    # Validate network
    if json_data['net'] not in list(NetworkType): return False

    # Validate core & rpc versioning format
    if not valid_version(json_data['version_rpc']) and not len(json_data['version_rpc']) == 0:
        return False

    if not valid_version(json_data['version_core']) and not len(json_data['version_core']) == 0:
        return False

    # Validate ip / domain for host
    if not valid_host(json_data['host']): return False

    # Validate port
    if not valid_port(json_data['port']): return False
    
    return True


