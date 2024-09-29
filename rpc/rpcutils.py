
import logging
import requests

from enum import IntEnum
from typing import Literal

from coretc.utils.valid_data import valid_host, valid_port, valid_version

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


def make_rpc_request(url: str, json_data: dict | None = None, method: Literal['POST', 'GET'] = 'POST') -> dict:
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
        return {'error': f'Unable to connect to {url}'}
    except BaseException as e:
        logger.error(f'Exception when attempting to access {url}: {str(e)}')
        return {'error': f'Exception while accessing {url}: {str(e)}'}
    
    if r.status_code != 200:
        logger.warn(f'Got status code: {r.status_code}, when accessing {url}')
        return {'error': f'Invalid status code accessing {url}: {r.status_code}'}

    return r.json()

PEER_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        
        'net': {'type': 'number'},
        'version_rpc': {'type': 'string'},
        'version_core': {'type': 'string'},

        'host': {'type': 'string'},
        'port': {'type': 'integer'},

        'last_height': {'type': 'integer'},
        'last_seen': {'type': 'integer'},
        'last_status': {'type': 'number'},
        
        'ssl_enabled': {'type': 'boolean'}

    }
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


