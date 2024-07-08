
from typing import Mapping, List, Tuple

import os, re
from os.path import exists as fileExists
from os.path import isdir as isDirectory
from copy import deepcopy

import bson, json, logging

from coretc.utils.generic import dump_json

from coretc.blocks import Block

logger = logging.getLogger('tc-core')
   
# TODO: Error handling

class BlockStorage:
    def __init__(self, store_directory: str, blocks_per_file: int):
        
        logger.info(f'Initializing BlockStorage {store_directory}, blocksperfile={blocks_per_file}')

        self.store_dir = store_directory
        self.blocks_per_file = blocks_per_file

        self.block_cache: Mapping[int, Block] = {}
        
        self.height: int = -1
        self.initialize()

    def initialize(self):
        '''
        Used to initialize the block store height
        '''
        filenames: List[str] = []
        pattern = re.compile(r'^[0-9a-f]+\.dat$')
        
        if not fileExists(self.store_dir) or not isDirectory(self.store_dir):
            os.makedirs(self.store_dir)

        filenames = [f for f in os.listdir(self.store_dir) if pattern.match(f)]
        
        if len(filenames) == 0:
            self.height = 0
            return

        # Get the block count of the last file
        block_count, _ = self.get_storefile_json(len(filenames) - 1)
        logger.info(f'Last block file contains {block_count} blocks')
        
        if block_count <= 0:
            logger.critical(f'Error initializing block store, invalid file: {len(filenames) - 1}')
            return

        self.height = (len(filenames) - 1)*self.blocks_per_file + block_count
    
    def store_blocks(self, blocks: List[Block]) -> bool:
        '''
        Get a list of blocks and add them to the store

        Args:
            blocks (List[Block]): List of blocks to force-save
        Return:
            bool: Whether the storing was successful

        '''   
        # Needed since the list will be modified
        to_add: List[Block] = deepcopy(blocks)
        added_count: int = 0
        
        # Iterate through the blocks in chucks, according to the block height
        while len(to_add) > 0:
            cut = self.blocks_per_file - (self.height % self.blocks_per_file)

            chunk = to_add[0:cut]
            to_add = to_add[cut:]

            store_file = (self.height + len(chunk) - 1) // self.blocks_per_file
            #print(f'Writting to store file {store_file}')

            # Handle possible other data in preexisting store file
            prev_data = []
        
            if self.store_file_exists(store_file):
                _, prev_data = self.get_storefile_json(store_file)
           
            if len(prev_data) + len(chunk) > self.blocks_per_file:
                logger.critical('INVALID STORE FILE SIZES!')

            for blk in chunk:
                prev_data.append(blk.to_json())
            
            self.save_to_storefile(store_file, {'blocks': prev_data})

            self.height += len(chunk)
        
        return True
    
    def store_file_exists(self, storefile: str | int) -> bool:
        '''
        Check if a storefile exists

        Args:
            storefile (str | int): If it's in INT form it will be parsed into the str
        Returns:
            bool: Whether the store exists
        '''

        if isinstance(storefile, int):
            storefile = f'{hex(storefile)[2:]}.dat'
        return fileExists(self.store_dir + storefile) and not isDirectory(self.store_dir + storefile)


    def get_storefile_json(self, storefile: str | int) -> Tuple[int, List]:
        '''
        Used to get the JSON of a given store file

        Args:
            storefile (str | int): If it's in INT form it will be parsed into the str
        Returns:
            Tuple[int, List]: Tuple of the block count and list of block json objects
        '''
        
        if isinstance(storefile, int):
            storefile = f'{hex(storefile)[2:]}.dat'

        with open(self.store_dir + storefile, 'rb') as f:
            results = bson.loads(f.read())
        
        #print(results['blocks'])

        if 'blocks' not in results or not isinstance(results['blocks'], list):
            logger.critical(f'Malformed JSON for block store file {storefile}')
            return (-1,[])

        return (len(results['blocks']), results['blocks'])
    
    def save_to_storefile(self, storefile: str | int, json_data: dict) -> bool:
        if isinstance(storefile, int):
            storefile = f'{hex(storefile)[2:]}.dat'

        with open(self.store_dir + storefile, 'wb') as f:
            f.write(bson.dumps(json_data))

        return True

    def get_stored_blockcount(self) -> int:
        return self.height
