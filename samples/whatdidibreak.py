import json
import os,sys,time, logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc.settings import ChainSettings

from coretc.utils.generic import data_hexdigest
from coretc import Chain, Block, mine_block
from coretc import TX, UTXO

logger = logging.getLogger('samplelog')

def create_example_utxo(is_input: bool = False) -> UTXO:
    return UTXO(b'A'*91, 0.5, 0, b'i'*32 if is_input else b'', b'I am in pain' if is_input else b'')
    
def main():

    # The error is obvs in the utxo shit
    test = TX([], [create_example_utxo()]).make()

    logger.debug(data_hexdigest(test.get_txid()))

    test_json = test.to_json()

    deserialized = test.from_json(test_json)
    
    logger.debug(json.dumps(test_json['outputs'], indent = 4))
    logger.debug(f'Original hash: {data_hexdigest(test.outputs[0].hash_sha256())}')
    logger.debug(test.outputs[0])

    if deserialized is None:
        logger.error('Error deserializing')
        return

    logger.debug(data_hexdigest(deserialized.get_txid()))

    deserialized_json = deserialized.to_json()



    


if __name__ == '__main__': main()

