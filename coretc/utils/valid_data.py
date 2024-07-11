
import re

from os.path import exists, isdir

DNS_REG = re.compile(r"""
    ^(?!-)(?!.*--)[A-Za-z0-9-]{1,63}(?<!-)\.
    (?:[A-Za-z0-9-]{1,63}\.)*
    (?:[A-Za-z]{2,})$
""", re.VERBOSE)

IP_REG = re.compile(r'\b((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b', re.VERBOSE)

USERNAME_REG = re.compile(r'^[0-9A-Za-z+_-]*')

def valid_ipv4(ip: str) -> bool: 
    '''
    Checks if the given input is an IPv4

    Args:
        ip (str): String to check

    Returns:
        bool: Whether the string matches the ipv4 format
    '''
    return IP_REG.match(ip) is not None

def valid_host(host: str) -> bool:
    '''
    Checks if the given string is an IPv4 or a DNS name

    Args:
        host (str): String to check

    Returns:
        bool: Whether it is an IPv4 or DNS name
    '''
    return IP_REG.match(host) is not None or DNS_REG.match(host) is not None

def valid_port(port: int | str) -> bool:
    '''
    Make sure a given port is valid. This also checks in case the port is in str form.

    Args:
        port (int | str): Given port to make sure is valid

    Returns:
        bool: Whether it's valid or not
    '''

    if isinstance(port, str):
        if not port.isdigit(): return False
        
        port = int(port)

    return port > 0 and port < 65535

def valid_directory(dir: str) -> bool:
    '''
    To return true the path must exist and be a directory

    Args:
        dir (str): The path

    Returns:
        bool: You know the drill
    '''

    return exists(dir) and isdir(dir)

def valid_file(filepath: str) -> bool:
    '''
    To return true the path must exist and not be a directory
    
    Args:
        filepath (str): The path

    Returns:
        bool: You know the drilll
    '''
    return exists(filepath) and not isdir(filepath)

def valid_username(username: str) -> bool:
    # This is only used in the setup wizard for nodes but fuck it
    if len(username) > 20: return False

    return USERNAME_REG.match(username) is not None
