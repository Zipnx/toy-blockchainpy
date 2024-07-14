
from typing import List, MutableMapping
import logging, json

from os.path import exists as fileExists
from os.path import isdir as isDirectory

from coretc import TX

logger = logging.getLogger('tc-core')

class MemPool:
    def __init__(self, mempool_file: str):

        self.mempool_file = mempool_file

        # TX -> Timestamp
        self.mempool: MutableMapping[TX, int] = {}

    def load_mempool(self) -> bool:
        '''
        Load the mempool from storage

        Returns:
            bool: Whether loading was successful
        '''
        logger.info(f'Loading MemPool from {self.mempool_file}')

        self.mempool.clear()

        if not fileExists(self.mempool_file) or isDirectory(self.mempool_file):
            logger.error('MemPool file not found')
            return False

        with open(self.mempool_file, 'rb') as f:
            json_data = json.load(f)
            
        for timestamp, txjson in json_data.items():
            tx_obj: TX | None = TX.from_json(txjson)

            if tx_obj is None:
                logger.critical('Malformed TX in MemPool file!')
                
                return False
            
            if not isinstance(timestamp, int):
                logger.critical('Malformed TX timestamp in MemPool file!')

                return False

            self.mempool[tx_obj] = timestamp

        logger.debug(f'Loaded {len(self.mempool)} TXs from MemPool file.')
        return True

    def save_mempool(self) -> bool:
        '''
        Store the mempool in the corresponding file

        Return:
            bool: Status
        '''

        logger.info(f'Saving MemPool data to {self.mempool_file}')

        if isDirectory(self.mempool_file):
            return False

        data = {}

        for transaction, stamp in self.mempool.items():
            data[stamp] = transaction.to_json()

        with open(self.mempool_file, 'w') as f:
            json.dump(data, f, indent = 4)

        return True

    def add_transaction(self, timestamp: int, transaction: TX) -> bool:
        self.mempool[transaction] = timestamp
        return True

    def remove_transaction(self, txid: bytes) -> bool:
        '''
        Remove a transaction from the mempool, identified by it's transaction ID
        
        Args:
            txid (bytes): Transaction id
        Returns:
            bool: Whether the deletion was successful
        '''

        for transaction in list(self.mempool.keys()).copy():
            
            if transaction.get_txid() == txid:
                del self.mempool[transaction]
                return True

        return False

