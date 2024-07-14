
import os,sys,argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rpc import RPC
from rpc.settings import RPCSettings, load_config

import logging
from flask import Flask, Response, json, jsonify, request

logger = logging.getLogger('chain-rpc')

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

@app.route('/getblock')
def get_block():
    '''
    Get an individual block, given it's difficulty

    TODO: I don't know if I necessarily like this, might be too heavy on the node
    '''

    req_data = request.get_json()

    if 'height' not in req_data:
        return error_response('Invalid response')


    target_height = req_data['height']

    if not isinstance(target_height, int):
        if not str(target_height).isdigit(): return error_response('Height must be in int form')
        
        target_height = int(target_height)

    if target_height < 0:
        return error_response('Target height must be >= 0')

    return jsonify(rpc.get_block(target_height))

@app.route('/getblocks')
def get_blocks_bulk():
    '''
    Gets a chunk of blocks
    '''
    return error_response('Unimplemented')

@app.route('/getblockhash')
def get_blockhash():
    '''
    Retrieves the hash of a block at a certain height
    '''
    return error_response('Unimplemented')

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

def main():

    if settings is None: return

    flask_log = logging.getLogger('werkzeug')
    flask_log.setLevel(logging.ERROR)
    
    logger.info(f'Node running at {settings.host}:{settings.port}')

    app.run(host = settings.host, port = settings.port, debug = False)

if __name__ == '__main__':
    main()
