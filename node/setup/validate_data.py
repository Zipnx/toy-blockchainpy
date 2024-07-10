
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
    return IP_REG.match(ip) is not None

def valid_host(host: str) -> bool:
    return IP_REG.match(host) is not None or DNS_REG.match(host) is not None

def valid_port(port: int) -> bool:
    return port > 0 and port < 65535

def valid_directory(dir: str) -> bool:
    return exists(dir) and isdir(dir)

def valid_username(username: str) -> bool:
    if len(username) > 20: return False

    return USERNAME_REG.match(username) is not None
