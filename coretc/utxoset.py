
from typing import List, dataclass_transform

from os.path import exists as fileExists
from os.path import isdir as isDirectory
import bson, json

from coretc.utxo import UTXO

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
        
        if not fileExists(self.outfile) or isDirectory(self.outfile):
            return False
        
        with open(self.outfile, 'rb') as f:
            data_raw = f.read()

            if len(data_raw) == 0: return True

            data = bson.loads(data_raw)

        if 'height' not in data or 'outputs' not in data:
            return False

        if not data['height'].isdigit(): return False

        self.currently_scanned_height = int(data['height'])

        for utxo_json in data['outputs']:

            utxo_obj = UTXO.from_json(utxo_json)

            if utxo_obj is None:
                return False

            self.utxos.append(utxo_obj)

        return True
    
    def get_as_json(self) -> dict:
        '''
        Get the whole set in JSON format
        '''

        output = {
            'height': self.currently_scanned_height,
            'outputs': []
        }

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

        if isDirectory(self.outfile):
            return False

        output = self.get_as_json()

        with open(self.outfile, 'wb') as f:

            data_raw = bson.dumps(output)

            f.write(data_raw)

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


