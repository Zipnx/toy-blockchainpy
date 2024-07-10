
from typing import List, Tuple
import configparser, bcrypt, json

def build_config(hostinfo: Tuple[str, int], 
                 node_directory: str, 
                 node_credentials: Tuple[str, str], 
                 peerlist: List[dict]) -> bool:

    '''
    Build the config file in the node_directory folder based on the given info

    Args:
        hostinfo (Tuple[str, str]): Tuple of the host interface & port
        node_directory str: Directory where the node config & data will be stored 
        node_credentials (Tuple[str, str]): The username & password combo for the node
        peerlist (List[dict]): List containing at least 1 peer the node will connect to

    Returns:
        bool: Whether the config creation was successful
    '''
    
    # First save the node config in the config.ini file
    config = configparser.ConfigParser()
    config.add_section('TC-Node')
    
    config.set('TC-Node', 'iface', hostinfo[0])
    config.set('TC-Node', 'port', str(hostinfo[1]))

    config.set('TC-Node', 'adminuser', node_credentials[0])
    
    salt = bcrypt.gensalt()

    config.set('TC-Node', 'adminpass', bcrypt.hashpw(
        node_credentials[1].encode('utf-8'),
        salt

    ).decode())
    
    with open(node_directory + '/config.ini', 'w') as f:
        config.write(f)

    # Then save the default peers to peers.json
    with open(node_directory + '/peers.json', 'w') as f:
        json.dump(peerlist, f, indent = 4)
    

    return True
