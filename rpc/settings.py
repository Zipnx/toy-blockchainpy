
from coretc.settings import ChainSettings

from typing import List
from dataclasses import dataclass, field

from os.path import exists as fileExists
from os.path import isdir  as isDirectory

import configparser, logging

logger = logging.getLogger('chain-rpc')

@dataclass(init = True)
class RPCSettings:
    node_directory: str = './node-data' 

    host: str = '127.0.0.1'
    port: int = 1993

    admin_username: str = 'admin'
    admin_passhash: str | None = None
    
    ssl_enabled: bool = False

    # TODO: Set these in the config wiz & file
    max_connections: int = 16

    def get_chainsettings(self) -> ChainSettings:
        '''
        Get the chain settings based on the node's settings

        Returns:
            ChainSettings: Settings object
        '''

        return ChainSettings(
            debug_log_dir = self.node_directory         + '/data/debug/',
            block_data_directory = self.node_directory  + '/data/blocks/',
            utxo_set_path = self.node_directory         + '/data/utxos.dat',
            mempool_path = self.node_directory          + '/data/mempool.dat'
        )

CONFIG_REQ = {
    'TC-Node': [
        'iface', 'port', 'adminuser', 'adminpass'
    ]
}

def load_config(node_directory: str) -> RPCSettings | None:
    '''
    Load the Node's RPC settings given it's node directory

    Returns:
        RPCSettings | None: Settings object or None if there is an error
    '''
    
    logger.debug(f'Loading configuration from {node_directory}')

    if not fileExists(node_directory) or not isDirectory(node_directory):
        logger.critical('Invalid node directory')
        return None
    
    if node_directory[-1] == '/' or node_directory[-1] == '\\':
        node_directory = node_directory[:-1]

    if not fileExists(node_directory+'/config.ini') or isDirectory(node_directory+'/config.ini'):
        logger.critical('Node config.ini file does not exist')
        return None
    
    if not fileExists(node_directory+'/peers.json') or isDirectory(node_directory+'/peers.json'):
        logger.critical('Default peers file does not exist')
        return None

    config = configparser.ConfigParser()
    config.read(node_directory + '/config.ini')

    # Make sure the required settings are set

    logger.info('Verifying config structure')

    for sec, options in CONFIG_REQ.items():

        if not config.has_section(sec):
            logger.critical(f'Node config.ini has no {sec} section.')
            return None

        for option in options:
            if not config.has_option(sec, option):
                logger.critical(f'Node config.ini has no {sec}->{option} option.')
                return None

    # Read the settings
    iface  = config.get('TC-Node', 'iface')
    port   = config.getint('TC-Node', 'port')
    user   = config.get('TC-Node', 'adminuser')
    pwhash = config.get('TC-Node', 'adminpass') 
    
    logger.debug('Config loaded.')

    return RPCSettings(
        node_directory = node_directory,
        host = iface, port = port,
        admin_username = user,
        admin_passhash = pwhash
    ) 
