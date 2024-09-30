
import os,sys,argparse, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc.utils.generic import data_hexdigest, data_hexundigest, is_valid_digit
from rpc import RPC
from rpc.settings import RPCSettings, load_config

import logging
from flask import Flask, Response, json, jsonify, request

logger = logging.getLogger('chain-rpc')
urllib_log = logging.getLogger('urllib3.connectionpool')
urllib_log.setLevel(logging.CRITICAL)


parser = argparse.ArgumentParser(description = 'Run a toychain node')
parser.add_argument('directory', type = str, help = 'Directory of the node, containing the config and blockchain data')

args = parser.parse_args()

app = Flask(__name__)

settings: RPCSettings | None = load_config(args.directory)

if settings is None:
    logger.critical('Unable to load settings!')
    quit()

rpc = RPC(settings)

def error_response(error_msg: str) -> Response:
    '''
    Just construct a standard error response
    
    Args:
        error_msg (str): Error message
    Returns:
        json: Flask json data
    '''

    return jsonify({'error': error_msg})

@app.route('/')
def homepage():
    '''
    The / page of the node should just return some basic stats and misc info
    '''
    return jsonify(rpc.get_info())

@app.route('/peers')
def get_peers():
    '''
    Return a list of connected peers
    '''
    return jsonify(rpc.get_peers_json())

@app.route('/height')
def get_current_height():
    '''
    Returns the node's top height
    '''
    return jsonify({
        'height': rpc.get_chain_height()
    }) 

@app.route('/estabheight')
def get_established_height():
    '''
    Returns the node's established height
    * Meaning, blocks that have been confirmed in the network and are not in a fork
    '''
    return jsonify({
        'height': rpc.chain.get_established_height()
    })


@app.route('/tophash')
def tophash():
    '''
    Returns the node's top hash
    '''
    return jsonify({
        'tophash': rpc.get_top_hash()
    }) 

@app.route('/topdifficulty')
def top_difficulty():
    '''
    Returns the node's top difficulty
    '''
    return jsonify({'difficulty': rpc.get_top_diff()})

@app.route('/getblock', methods = ['POST'])
def get_block():
    '''
    Get an individual block, given it's difficulty

    TODO: I don't know if I necessarily like this, might be too heavy on the node
    '''

    req_data = request.get_json()

    if 'height' not in req_data:
        return error_response('Invalid request')


    target_height = req_data['height']
    
    if not is_valid_digit(target_height):
        return error_response('Height must be in int form')

    target_height = int(target_height)

    if target_height <= 0:
        return error_response('Target height must be >= 1')

    return jsonify(rpc.get_block(target_height))

@app.route('/getblocks', methods = ['POST'])
def get_blocks_bulk():
    '''
    Gets a chunk of blocks
    '''

    req_data = request.get_json()

    if 'height' not in req_data or 'count' not in req_data:
        return error_response('Invalid request')

    target_height = req_data['height']
    target_count  = req_data['count']

    if not is_valid_digit(target_height):
        return error_response('Height must be in int form')

    if not is_valid_digit(target_count):
        return error_response('Count must be in int form')

    target_height = int(target_height)
    target_count = int(target_count)
    
    if target_height <= 0:
        return error_response('Target height must be >= 1')

    if target_count <= 0:
        return error_response('Target count must be >= 1')

    if target_count > 256:
        return error_response('Cannot get more than 256 blocks at a time')

    return jsonify(rpc.get_blocks(target_height, target_count))

@app.route('/getblockhash', methods = ['POST'])
def get_blockhash():
    '''
    Retrieves the hash of a block at a certain height
    '''
    req_data = request.get_json()

    target_height = req_data['height']

    if not isinstance(target_height, int):
        if not str(target_height).isdigit(): return error_response('Height must be in int form')
        
        target_height = int(target_height)

    if target_height <= 0:
        return jsonify({
            'hash': data_hexdigest(b'\x00'*32, no_prefix = False)
        })
    
    block_json = rpc.get_block(target_height)
    
    if 'error' in block_json: 
        return jsonify(block_json)

    return jsonify({
        'hash': block_json['hash']
    })

@app.route('/submitblock', methods = ['POST'])
def submit_block():
    '''
    Used to submit a block to the node
    If the block is accepted it will be propagated to other peers
    '''
    if request.method == 'GET':
        return jsonify({'msg': 'This endpoint is POST only'})
    
    block_data = request.get_json()

    return jsonify(rpc.add_block(block_data))

@app.route('/submittx')
def submit_transaction():
    '''
    Used to submit a transaction to the node
    If the tx is valid it will be propagated to other peers
    '''
    return error_response('Unimplemented')

@app.route('/getmempool')
def get_mempool():
    '''
    Retrieves the node's current mempool of txs
    '''
    
    return error_response('Unimplemented')

@app.route('/tophashexists', methods = ['POST'])
def check_tophash_exists():
    '''
    Checks if a given hash in hex format corresponds to one of the hashes 
    in the top of the RPC's chain
    '''

    req_data = request.get_json()

    if 'hash' not in req_data:
        return error_response('No hash specified')

    hash_bytes = data_hexundigest(req_data['hash'])

    return jsonify(rpc.check_tophash_exists(hash_bytes))

# This endpoint is the called by peers wanting to make themselves known to this peers
# TODO: They undergo certain verification which will be improved later on

'''
How it would probably go

A -> B hellopeer
    Data sent:
        1. Height & Top hash
        2. A's node port
        3. Personal info (network type main / test net, etc...)

A <- B Asks for the block info at some random heights 

A -> B Responds with valid info

Now B sends a hellopeer to repeat the process and as a result they are now acquainted

Afterwards both nodes share their peer nodes

TODO: 
In future for network balancing if 2 nodes share alot of peers or are in the same sort of
"sub-network" they should prioritize peering with more foreign nodes. 
Graph theory strikes again

'''


@app.route('/hellopeer', methods = ['POST'])
def peer_init():
    
    # TODO: Will remain unimplemented until i make the peer manager cause this is turning
    #       into a rats nest
    return error_response('Unimplemented')

@app.route('/ping', methods = ['POST'])
def pong():
    return jsonify({
        'msg': 'pong',
        'stamp': int(time.time())
    })

def main():

    if settings is None: return

    flask_log = logging.getLogger('werkzeug')
    flask_log.setLevel(logging.ERROR)

    
    
    logger.info(f'Node running at {settings.host}:{settings.port}')

    app.run(host = settings.host, port = settings.port, debug = False)

if __name__ == '__main__':
    main()
