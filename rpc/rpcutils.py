
import logging
import requests

from typing import Literal
from .peers import Peer

logger = logging.getLogger('chain-rpc')

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
        


