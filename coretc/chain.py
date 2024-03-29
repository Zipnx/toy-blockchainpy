
from typing import List, Tuple

from coretc.forktree import ForkBlock
from coretc.blocks import Block
from coretc.utils.generic import data_hexdigest
from coretc.utxo import UTXO
from coretc.status import BlockStatus
from coretc.utils.list_utils import CombinedList
from coretc.settings import ChainSettings
from coretc.utxoset import UTXOSet

from binascii import hexlify
import json, time

import logging

logger = logging.getLogger('tc-core')

# Possibly split the logger into further submodules

class Chain:
    '''
    Chain Core Class 
    Handles the addding of new blocks & verification
    '''

    def __init__(self, settings: ChainSettings) -> None:
        '''
        Initialize a new chain
        '''
        
        logger.debug('Initialized new chain')
        
        self.opts = settings

        self.initDifficulty = settings.initial_difficulty
        self.difficulty = settings.initial_difficulty
        self.blockreward = settings.initial_blockreward
        self.blocks: List[Block] = [] 

        self.forks: ForkBlock | None = None

        self.utxo_set: UTXOSet = UTXOSet(self.opts.utxo_set_path)
        
        # TODO: Do checks here
        self.utxo_set.load_utxos()

    def validate_transactions(self, block: Block, fork: ForkBlock | None) -> BlockStatus:
         
        reward_found = False
        
        if fork is not None:
            fork_used, fork_added = fork.get_fork_utxoset()
        else:
            fork_used = []
            fork_added = []

        # Utilized to make sure no 2 transactions use the same UTXO
        utxos_used: List[UTXO] = list()

        for transaction in block.transactions:
            
            #print(json.dumps(transaction.to_json(), indent = 4))

            if len(transaction.inputs) == 0:
                if reward_found: return BlockStatus.INVALID_TX_MULTIPLE_REWARDS
                reward_found = True

                # Check reward amount
                if transaction.outgoing_funds() > self.get_top_blockreward():
                    return BlockStatus.INVALID_TX_WRONG_REWARD_AMOUNT

            # Check UTXOs and TX Forms
            if not transaction.check_inputs():
                return BlockStatus.INVALID_TX_INPUTS

            if not transaction.check_outputs():
                return BlockStatus.INVALID_TX_OUTPUTS

            # Check if the utxo's are even valid to spend
            for utxo in transaction.inputs:
            
                # Check if it has been used in a transaction of the current block / tx
                for check_utxo in utxos_used:
                    if check_utxo.compare_as_input(utxo):
                        logger.warn(f'Input utxo of {data_hexdigest(transaction.get_txid())} spent in current fork')
                        return BlockStatus.INVALID_TX_UTXO_IS_SPENT

                utxos_used.append(utxo)

                # First check the utxo set
                utxo_in_set: UTXO | None = self.utxo_set.utxo_get(utxo.txid, utxo.index)
                
                if utxo_in_set is not None:
                    if not utxo_in_set.compare_as_input(utxo):
                        # The utxo has some modifications that make it invalid
                        logger.warn(f'Input utxo of {data_hexdigest(transaction.get_txid())} present in utxoset but modified')
                        return BlockStatus.INVALID_TX_UTXO_IS_SPENT
                    
                    # Remember to check if it's used in the fork

                    for fork_utxo in fork_used:
                        if fork_utxo.compare_as_input(utxo):
                            logger.warn(f'Input utxo of {data_hexdigest(transaction.get_txid())} present in utxoset but used in fork')
                            return BlockStatus.INVALID_TX_UTXO_IS_SPENT

                    continue
                
                # Then check the fork's set
                
                # I hate this solution but fuck it
                found = False
                for fork_utxo in fork_added:
                     
                    if fork_utxo.compare_as_input(utxo):
                        found = True
                        break

                if found: continue

                logger.warn(f'Input utxo of {data_hexdigest(transaction.get_txid())} does not exist.')

                print(fork_added)

                return BlockStatus.INVALID_TX_UTXO_IS_SPENT

            # Note: If a TX uses a UTXO created in the same block this will reject it
            
            

        return BlockStatus.VALID

    def is_block_valid(self, block: Block, fork: ForkBlock | None) -> BlockStatus:
        '''
        Given a block, check if it's valid. Also verifies in a side chain

        Return:
            bool: Block validity
        '''
        
        # TODO: Difficulty changes depending on the additional chain, also the UTXO set (to be implemented)
        
        block_hash = block.hash_sha256()
        
        # Check if the block is a duplicate already in the fork tree
        if self.forks is not None and block_hash in self.forks.hash_cache:
            return BlockStatus.INVALID_DUPLICATE
        
        
        if fork is not None:
            additional_chain = fork.get_block_route()
        else:
            additional_chain = []

        reference_chain: CombinedList = CombinedList(self.blocks, additional_chain)

        logger.info(f'Checking validity of block: 0x{hexlify(block_hash).decode()}')
        
        ### CHECK THE PREVIOUS HASH ###

        if len(reference_chain) == 0:
            if not block.previous_hash == b'\x00'*32:
                return BlockStatus.INVALID_PREVHASH
        else:
            if not block.previous_hash == reference_chain[-1].hash_sha256():
                return BlockStatus.INVALID_PREVHASH
        
        ### CHECK IF THE DIFFICULTY LEVEL IS VALID ###
        if not block.difficulty_bits == self.difficulty:
            logger.warn('Block Invalid: Incorrect difficulty level')
            return BlockStatus.INVALID_DIFFICULTY
        
        ### CHECK IF THE BLOCK HASH IS VALID ###
        if not block.is_hash_valid():
            logger.warn('Block Invalid: Incorrect PoW hash')
            return BlockStatus.INVALID_POW

        ### CHECK THE TRANSACTIONS VALIDITY ###
        if (res := self.validate_transactions(block, fork)) == BlockStatus.VALID:
            logger.debug('Block and TXs validated successfully')
        else:
            logger.warn('Block TXs invalid')


        return res

    def add_block(self, newBlock: Block) -> BlockStatus:
        '''
        Try to add a new block in the current chain

        Args:
            newBlock (Block): New block to add

        Return:
            BlockStatus: Status enum, indicates possible errors

        '''
        
        ### Check if there even is a fork (will happen if the chain is empty, probably)
        if self.forks is not None:
            forkblock: ForkBlock | None = self.forks.get_block_by_hash(newBlock.previous_hash)
        else:
            forkblock = None
        
        ### If the selected fork block whose hash is this block's previous hash,
        ### the chain route is the list of blocks in order from the tree root to the forkblock
        
        
        validity = self.is_block_valid(newBlock, fork = forkblock)
        
        logger.debug(f'Validation result: {validity}')

        
        if not validity == BlockStatus.VALID:
            return validity
        
        # In the case where a fork is not present, it needs to be created with the new block as the root

        if forkblock is None:
            self.forks = ForkBlock(None, newBlock)
            # This is probably the worst shit ive written in a while
            self.forks.hash_cache[newBlock.hash_sha256()] = self.forks
        else:
            
            if self.forks is None:
                return BlockStatus.INVALID_ERROR

            fb = forkblock.append_block(newBlock)
            self.forks.hash_cache[newBlock.hash_sha256()] = fb

        merged = self.attempt_merge()

        if merged > 0:
            logger.debug(f'Merged {merged} blocks.')
        

        return validity
    
    def attempt_merge(self) -> int:
        '''
        Attempt to merge some blocks from the fork tree over to the list of permanently added
        blocks

        Return:
            int: Count of blocks merged over
        '''

        # TODO: Again, terrible inefficiencies, can be fixed with some caching

        if self.forks is None: return 0
        
        tree_height = self.forks.get_tree_height()
        linear_height = self.forks.get_linear_count()
        current: ForkBlock = self.forks
        mergers = 0

        if tree_height <= 6: return 0
        
        logger.info('Merging Blocks from fork tree into the chain')
        
        # Tf was i thinking while writing this shit
        if linear_height >= 3:
            for _ in range(linear_height - 1):
                self.forks = self.forks.next[0]
            
            self.update_utxoset_from_fork(self.forks.parent) # i hate myself and i hate this, this ALL NEEDS TO BE CLEARED
            self.forks.parent = None

            self.forks.regenerate_heights()
            self.forks.regenerate_cache()
            return linear_height - 1

        while tree_height >= 3:
            if current.is_node_balanced(): break 
            
            self.blocks.append(current.block)
            mergers += 1
            current = current.get_tallest_subtree()
            
            if current is None:
                print('???')
                break

            tree_height -= 1
        
        # Add the modifications to the utxo set to the actual utxo_set
        # .parent accessible because the gc hasnt kicked in yet
        
        self.update_utxoset_from_fork(current.parent)

        self.forks = current
        self.forks.parent = None # Hopefully this will cause the objects to be cleared by the gc, but idfk
        self.forks.regenerate_heights()
        self.forks.regenerate_cache() # Performance hit

        return mergers
    
    def merge_all(self) -> int:
        '''
        Forcefully merge all blocks in the fork tree
        NOTE: This should not be routinely used

        Return:
            int: Number of blocks merged
        '''
        logger.info('Merging all Blocks from fork tree into the chain')
        
        if self.forks is None: return 0

        leaf: ForkBlock = self.forks.get_tallest_leaf()
        self.forks = None

        return self.commit_fork(leaf)
    
    def commit_fork(self, fork: ForkBlock) -> int:
        '''
        Given a ForkBlock leaf, add the route blocks into permanent storage and update the utxo set

        Args:
            fork (ForkBlock): Fork which's path will be commited
        Return:
            int: Total commits
        '''

        blocks: List[Block] = fork.get_block_route()
        self.update_utxoset_from_fork(fork)

        for blk in blocks:
            self.blocks.append(blk)

        return len(blocks)

    def update_utxoset_from_fork(self, fork: ForkBlock) -> None:
        '''
        Used to update the UTXO set with data including this fork,

        Args:
            fork (ForkBlock): The fork in question
        Return:
            None: Should probably return _something_ but we'll get there when we get there
        '''

        logger.info('Updating UTXO Set with new data from fork')
        utxos_used, utxos_added = fork.get_fork_utxoset()

        for utxo in utxos_used:
            if not self.utxo_set.utxo_remove(utxo.txid, utxo.index):
                logger.critical('While updating the utxo set a used utxo was not present in the set?')

        for utxo in utxos_added:
            # these are already deepcopies
            if not self.utxo_set.utxo_add(utxo):
                logger.critical('While updating the utxo set a new utxo was invalid')


    def get_height(self) -> int:
        '''
        Get the total chain height
        NOTE: This must be made to include the stores blocks in the future

        Return:
            int: Total chain height
        '''

        height = len(self.blocks)
        
        # If a fork exists add it's top height to the total height returned
        if self.forks is not None:
            height += self.forks.get_tree_height()

        return height


    def get_top_blockreward(self) -> float:
        '''
        Return the current top block reward
        TODO: Also based on the fork data
        '''

        return self.blockreward

    def get_top_difficulty(self) -> int:
        '''
        Return the current difficulty bits of the chain
        TODO: Also based on the fork data

        Return:
            int: Difficulty bits
        '''
        
        return self.difficulty

    def get_tophash(self) -> bytes:
        '''
        Return the current top hash or zero-hash if the chain is empty
        Note: By top hash i mean the one of the block in the longest fork chain

        Return:
            bytes: 32 byte hash digest

        '''
        
        # This is horrendously inefficient, needs caching of the top hash when the block
        # is added

        if self.forks is None:
            # Will return the top hash of the blocks list in there is no active fork
            return self.blocks[-1].hash_sha256() if len(self.blocks) > 0 else b'\x00'*32
        
        current: ForkBlock | None = self.forks 

        while not len(current.next) == 0:
            current = current.get_tallest_subtree()

        return current.block.hash_sha256()

