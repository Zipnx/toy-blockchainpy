
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from node.rpc import RPC

import logging
from flask import Flask, jsonify, request

app = Flask(__name__)
rpc = RPC()

@app.route('/')
def homepage():
    return 'ToyChain RPC Running'

@app.route('/peers')
def get_peers():
    return jsonify(rpc.get_peer_list())

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

@app.route('/submitblock')
def submit_block():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/submittx')
def submit_transaction():
    return jsonify({'msg': 'Unimplemented'})

@app.route('/getmempool')
def get_mempool():
    return jsonify({'msg': 'Unimplemented'})

def main():
    flask_log = logging.getLogger('werkzeug')
    flask_log.setLevel(logging.ERROR)

    app.run(host = '127.0.0.1', port = 1993, debug = False)

if __name__ == '__main__':
    main()
