
import os,sys,argparse, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rich.console import Console
from rich.panel import Panel
from rich import print_json

import coretc.utils.valid_data as valid

import node.setup.wizard_widgets as widget
import node.setup.create_config as conf

def wizard(con: Console) -> tuple:
    con.print(Panel("ToyChain Node Configuration Setup Wizard"))
    
    while True:
        host = widget.get_string('Enter listening interface:', '0.0.0.0')
        
        if valid.valid_ipv4(host): break

        print('Invalid IP format.')

    while True:
        port = widget.get_int('Enter listening port:', 1993)
    
        if valid.valid_port(port): break

        print('Invalid port number.')

    while True:
        node_directory = widget.get_string(
            'Enter a storage directory for the new node:', 
            './node-data/'
        )

        if valid.valid_directory(node_directory): break

        print('Invalid directory selected.')
    
    while True:
        node_admin = widget.get_string(
            'Enter a username:',
            'admin'
        )

        if valid.valid_username(node_admin): break

        print('Invalid username')

    while True:
        node_pass = widget.get_password_and_verify('Enter a password: ')

        if node_pass is not None: break

        print('Invalid password.')

    con.print(Panel("Enter at least 1 peer to use."))

    peers = []

    while True:
        
        while True:
            peer_addr = widget.get_string('Enter peer IP/DNS')
        
            if valid.valid_host(peer_addr): break

            print('Invalid host selected.')

        while True:
            peer_port = widget.get_int('Enter peer port:', 1993)

            if valid.valid_port(peer_port): break

            print('Invalid port number.')
        
        peers.append({'host': peer_addr, 'port': peer_port})

        if not widget.get_yes_no('Do you wish to add another peer?', default = False):
            break

    return ( (host, port), node_directory, (node_admin, node_pass), peers )

def main():
    console = Console()

    # Configuration wizard
    try:
        host, nodedir, nodecreds, peers = wizard(console) 
    except KeyboardInterrupt:
        console.print('\nWizard operation cancelled by user.', style = 'bold red')
        return
    
    # Verify
    console.print(Panel("Verify Creation."))

    console.print(f'Host: {host[0]}:{host[1]}')
    console.print(f'Directory: {nodedir}')
    console.print(f'Credentials: {nodecreds[0]} = {"*"*len(nodecreds[1])}')

    console.print(f'Peers:')
    console.print(json.dumps(peers, indent = 4))
    
    proceed = widget.get_yes_no('\nDo you wish to proceed?', default = True)
    
    if not proceed:
        console.print('Operation cancelled.', style = 'bold red')
        return

    status = conf.build_config(host, nodedir, nodecreds, peers) 
    
    if status:
        console.print('Node configuration complete', style = 'bold green')
    else:
        console.print('Unable to save node configuration', style = 'bold green')

if __name__ == '__main__':
    main()
