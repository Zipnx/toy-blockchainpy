
from binascii import hexlify, unhexlify
import json

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

def dump_json(json_data: dict) -> None:
    print(json.dumps(json_data, indent = 4))
