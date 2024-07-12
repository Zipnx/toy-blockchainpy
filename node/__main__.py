
import os,sys,argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from node.rpc import RPC
from node.settings import RPCSettings, load_config

import logging
from flask import Flask, jsonify, request

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

@app.route('/')
def homepage():
    return jsonify(rpc.get_info())

@app.route('/peers')
def get_peers():
    return jsonify(rpc.get_peers_json())

@app.route('/height')
def get_current_height():
    return jsonify({
        'height': rpc.get_chain_height()
    }) 

@app.route('/tophash')
def tophash():
    return jsonify({
        'tophash': rpc.get_top_hash()
    }) 

@app.route('/topdifficulty')
def top_difficulty():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/getblock')
def get_block():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/getblocks')
def get_blocks_bulk():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/getblockhash')
def get_blockhash():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/submitblock', methods = ['POST'])
def submit_block():
    if request.method == 'GET':
        return jsonify({'msg': 'This endpoint is POST only'})
    
    block_data = request.get_json()

    return jsonify(rpc.add_block(block_data))

@app.route('/submittx')
def submit_transaction():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/getmempool')
def get_mempool():
    return jsonify({'msg': 'Unimplemented'})

def main():
    flask_log = logging.getLogger('werkzeug')
    flask_log.setLevel(logging.ERROR)
    
    logger.info(f'Node running at {settings.host}:{settings.port}')

    app.run(host = settings.host, port = settings.port, debug = False)

if __name__ == '__main__':
    main()
