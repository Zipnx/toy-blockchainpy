
from binascii import hexlify, unhexlify
import logging, json, bson

from os.path import exists as fileExists
from os.path import isdir as isDirectory

from coretc.utils.valid_data import valid_file, valid_directory

logger = logging.getLogger('tc-core')

def data_hexdigest(data: bytes, no_prefix: bool = False) -> str:
    '''
    Given a list of bytes return them in a hex format 0x...

    Args:
        data (bytes): Data to convert to hex format

    Return:
        str: Formatted hex string
    '''

    return f'{"0x" if not no_prefix else ""}{hexlify(data).decode()}'

def data_hexundigest(hexstring: str) -> bytes:
    '''
    Get a byte array from a hex encoded string

    Args:
        hexstring (str): Input string to decode

    Return:
        bytes: Decoded bytes
    '''

    hexstring = hexstring[(2 if hexstring[:2] == '0x' else 0):]

    return unhexlify(hexstring)

def load_json_from_file(filename: str, verbose: bool = False) -> dict | None:
    '''
    Attempt to load JSON data from a file

    Args:
        filename (str): File path to load from
        verbose (bool): Default is True. Whether to display messages or not
    Returns:
        dict | None: Either the JSON as a python dictionary or None if an error occured
    '''
    
    if not valid_file(filename):
        if verbose:
            logger.error(f'File {filename} unavailable to load JSON')
        return None

    try:
        with open(filename, 'r') as f:
            raw_data = f.read()
        
    except BaseException as e:
        if verbose:
            logger.critical(f'Unknown error loading JSON data from {filename}: {str(e)}')
        return None

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError or ValueError or TypeError or UnicodeDecodeError:
        if verbose:
            logger.critical(f'File {filename} contains invalid JSON')
        return None
    except BaseException as e:
        if verbose:
            logger.critical(f'Unknown error parsing JSON data from {filename}: {str(e)}')

        return None

    return data

def load_bson_from_file(filename: str, verbose: bool = True) -> dict | None:
    '''
    Attempt to load BSON data from a file

    Args:
        filename (str): File path to load from
        verbose (bool): Default is True. Whether to display messages or not
    Returns:
        dict | None: Either the resulting JSON as a python dictionary or None if an error occured
    '''
    
    if not valid_file(filename): 
        if verbose:
            logger.error(f'File {filename} unavailable to load BSON')

        return None

    try:
        with open(filename, 'rb') as f:
            raw_data = f.read()
        
    except BaseException as e:
        if verbose:
            logger.critical(f'Unknown error loading BSON data from {filename}: {str(e)}')
        return None
    
    try:
        data = bson.loads(raw_data)
    except BaseException as e:
        if verbose:
            logger.critical(f'Error passing BSON from {filename}: {str(e)}')
        return None
    
    return data

def dump_json(json_data: dict) -> None:
    print(json.dumps(json_data, indent = 4))
