
from typing import List, dataclass_transform

from os.path import exists as fileExists
from os.path import isdir as isDirectory
import bson, json

from coretc.utils.generic import load_bson_from_file, load_json_from_file
from coretc.utxo import UTXO
import logging

logger = logging.getLogger('tc-core')

class UTXOSet:
    def __init__(self, store_file: str):

        self.outfile = store_file
        
        self.utxos: List[UTXO] = []
        
        self.currently_scanned_height: int = -1

    def load_utxos(self) -> bool:
        '''
        Load the UTXO set from the selected store file
        
        Return:
            bool: Whether the loading was successful
        '''
        logger.info(f'Loading UTXO set from {self.outfile}')
        
        self.utxos.clear()
        
        data = load_bson_from_file(self.outfile, verbose = True)

        if data is None:
            logger.error('Error loading UTXOSet data from file!')
            return False

        if 'height' not in data or 'outputs' not in data:
            logger.error('UTXO Set file contains invalid data!')
            return False

        self.currently_scanned_height = int(data['height'])

        for utxo_json in data['outputs']:

            utxo_obj = UTXO.from_json(utxo_json)

            if utxo_obj is None:
                logger.error('Error parsing UTXO in file: {utxo_json}')
                return False

            self.utxos.append(utxo_obj)
        
        logger.debug(f'Loaded {len(self.utxos)} from {self.outfile}')

        return True
    
    def get_as_json(self) -> dict:
        '''
        Get the whole set in JSON format
        '''
        
        output: dict = {}
        output['height'] = self.currently_scanned_height
        output['outputs'] = list()

        for utxo in self.utxos:

            utxo_json = utxo.to_json(is_input = False)

            output['outputs'].append(utxo_json)

        return output

    def save_utxos(self) -> bool:
        '''
        Store the memory loaded utxo set into the specified file

        Return:
            bool: Whether the saving was successful
        '''
        
        logger.info(f'Saving UTXO set to {self.outfile}')

        if isDirectory(self.outfile):
            return False

        output = self.get_as_json()

        with open(self.outfile, 'wb') as f:

            data_raw = bson.dumps(output)

            f.write(data_raw)
            
        logger.debug(f'Saved {len(self.utxos)} UTXOs to file')

        return True
    
    def utxo_exists(self, txid: bytes, index: int) -> int:
        '''
        Get the index of a utxo if it exists, else return -1

        Return:
            int: Index in the utxos list
        '''
        for idx, utxo in enumerate(self.utxos.copy()):
            
            if utxo.txid == txid and utxo.index == index:
                self.utxos.pop(idx)
                return idx
        
        return -1

    def utxo_remove(self, txid: bytes, index: int) -> bool:
        '''
        Remove a UTXO from the set, given it's txid and index

        Return:
            bool: Whether the deletion was successful
        '''

        list_index = self.utxo_exists(txid, index)

        if list_index < 0: return False

        self.utxos.pop(list_index)

        return True

    def utxo_get(self, txid: bytes, index: int) -> UTXO | None:
        '''
        Get a utxo given it's txid and index
        If the utxo does not exist returns None
        '''

        list_index = self.utxo_exists(txid, index)

        if list_index < 0: return None

        return self.utxos[list_index]

    def utxo_add(self, utxo: UTXO) -> bool:
        '''
        Attempt to add a utxo in the utxo set. If the utxo does not have proper fields this will return False
        NOTE: This does not handle duplicate additions

        Args:
            utxo (UTXO): The utxo object to add to the set
        Return:
            bool: Whether the addition succeded
        '''

        if not utxo.is_valid() or not len(utxo.txid) == 32: return False 

        self.utxos.append(utxo)
        return True

    def utxo_count(self) -> int:
        return len(self.utxos)
