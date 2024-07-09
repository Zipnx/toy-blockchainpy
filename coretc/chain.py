
from typing import List, Tuple

from coretc.difficulty import adjustDifficulty
from coretc.forktree import ForkBlock
from coretc.blocks import Block
from coretc.utils.errors import deprecated, incomplete
from coretc.utils.generic import data_hexdigest, dump_json
from coretc.utxo import UTXO
from coretc.status import BlockStatus
from coretc.utils.list_utils import CombinedList
from coretc.settings import ChainSettings
from coretc.utxoset import UTXOSet
from coretc.blockstorage import BlockStorage
from coretc.mempool import MemPool

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
        self.settings = settings
        logger.debug('Initialized new chain')
        
        self.opts = settings

        self.difficulty = settings.initial_difficulty
        self.blockreward = settings.initial_blockreward
        self.blocks: List[Block] = [] 

        self.forks: ForkBlock | None = None
        
        self.block_store: BlockStorage = BlockStorage(settings.block_data_directory,
                                                      settings.blocks_per_store_file)
        if self.block_store.height > 0:
            self.difficulty = self.block_store.get_store_topdiff()
    
        self.utxo_set: UTXOSet = UTXOSet(self.opts.utxo_set_path)
        
        # TODO: Do checks here
        self.utxo_set.load_utxos()

        self.memory_pool: MemPool = MemPool(self.opts.mempool_path)
        self.memory_pool.load_mempool()

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
            if self.block_store.height > 0:
                if not block.previous_hash == self.block_store.get_store_tophash():
                    return BlockStatus.INVALID_PREVHASH

            else:
                if not block.previous_hash == b'\x00'*32:
                    return BlockStatus.INVALID_PREVHASH
        else:
            if not block.previous_hash == reference_chain[-1].hash_sha256():
                return BlockStatus.INVALID_PREVHASH
        
        ### CHECK IF THE DIFFICULTY LEVEL IS VALID ###
        if not block.difficulty_bits == self.get_difficulty(fork):
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
        New merging function because the old one is dogshit, what was I thinking?

        Return:
            int: Count of blocks merged over
        '''
        
        if self.forks is None: return 0

        tree_height = self.forks.get_tree_height()
        current: ForkBlock = self.forks
        merge_count: int = 0

        # This new function will be much more grounded, overcomplicating the previous one
        # led to shit. This time we are going simple, if the tree is 6
        # merge 3 blocks, simpler

        if tree_height <= 5: return 0

        while tree_height > 3:
            # if the node is balanced there aint something we can do
            if current.is_node_balanced(): break

            self.blocks.append(current.block)
            merge_count += 1
            current = current.get_tallest_subtree()

            if current is None:
                logger.critical('Imma be real, no idea how this happened')
                break
            
            tree_height -= 1

        self.update_utxoset_from_fork(current.parent)
        self.forks = current
        logger.info(f'New fork root: {data_hexdigest(self.forks.block.hash_sha256())}')
        self.forks.parent = None

        self.forks.regenerate_heights()
        self.forks.regenerate_cache()
        
        # Update the established difficulty

        old_chunk = (self.get_established_height() - merge_count - 1) // self.settings.difficulty_adjustment
        new_chunk = (self.get_established_height() - 1) // self.settings.difficulty_adjustment

        if old_chunk < new_chunk and not self.get_established_height() < self.settings.difficulty_adjustment:

            logger.debug(f'Adjusting established difficulty for chunk {new_chunk}')
            
            newdiff = self.get_chunk_difficulty(new_chunk)
            logger.debug(f'New difficulty: {newdiff}')

            self.difficulty = newdiff

        '''
        # Update the established difficulty
        old_chunk = (self.get_established_height() - merge_count - 1) // self.settings.difficulty_adjustment
        new_chunk = (self.get_established_height() - 1) // self.settings.difficulty_adjustment
        
        print(old_chunk, new_chunk)

        if old_chunk < new_chunk and not self.get_established_height() < self.settings.difficulty_adjustment:
            chunk_start = (old_chunk * self.settings.difficulty_adjustment) + 1
            chunk_end   = new_chunk * self.settings.difficulty_adjustment

            logger.debug(f'Adjusting established difficulty {chunk_start} - {chunk_end}')

            start: Block | None = self.get_block_by_height(chunk_start)
            end:   Block | None = self.get_block_by_height(chunk_end)

            if (start is None or end is None):
                logger.critical(
                    f"Error calculating established difficulty of {chunk_start} and {chunk_end}")
            else:
                delta: int = end.timestamp - start.timestamp
                seconds_per_block = delta / self.settings.difficulty_adjustment
                seconds_per_block = max(seconds_per_block, 0.01)
                deviation = self.settings.target_blocktime / seconds_per_block

                self.difficulty = adjustDifficulty(self.difficulty, deviation)
                logger.debug(f'New difficulty: {hex(self.difficulty)}')
                logger.debug(f'Deviation: {deviation:.2f}')
        '''

        # Try to save block to the block store, should match the blocks per file ideally
        while len(self.blocks) > self.settings.blocks_per_store_file:
            chunk_size = self.settings.blocks_per_store_file - (self.block_store.height % self.settings.blocks_per_store_file)

            logger.debug(f'Permanently storing {chunk_size} blocks.')

            self.block_store.store_blocks(self.blocks[:chunk_size])

            self.blocks = self.blocks[chunk_size:]

        return merge_count

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

        logger.debug(f'Fork UTXO Total: {len(utxos_used)} Used, {len(utxos_added)} Added.')

        for utxo in utxos_used:
            if not self.utxo_set.utxo_remove(utxo.txid, utxo.index):
                logger.critical('While updating the utxo set a used utxo was not present in the set?')

        for utxo in utxos_added:
            # these are already deepcopies
            if not self.utxo_set.utxo_add(utxo):
                logger.critical('While updating the utxo set a new utxo was invalid')

    def get_block_by_height(self, target_height: int,
                            fork: ForkBlock | None = None, 
                            get_top_fork: bool = False) -> Block | None:
        '''
        Given a height value, retrieve the block at that given height

        Args:
            target_height (int): Height of block to retrieve
            fork (ForkBlock): Fork to utilize, none to not use a fork
            get_top_fork(bool): Get the difficulty accounting for the longest fork

        Returns:
            Block | None: Block object that was requested or none if there is no block at that height

        '''

        if target_height <= self.block_store.height:
            # Get from the stored block

            return self.block_store.get_block(target_height)
        
        if target_height <= self.get_established_height():
            # Get from the blocks list
            index = target_height - self.block_store.height - 1
            
            return self.blocks[index]
        
        if fork is None and not get_top_fork: return None

        if fork is not None:
            used_fork = fork
            route = used_fork.get_block_route()
        elif get_top_fork:
            used_fork, route = self.get_longest_fork()
        
        if used_fork is None or len(route) == 0: return None

        index = target_height - self.get_established_height() - 1
        
        if index >= len(route): return None

        return route[index]


    def get_height(self) -> int:
        '''
        Get the total chain height

        Return:
            int: Total chain height
        '''

        height = len(self.blocks) + self.block_store.height
        
        # If a fork exists add it's top height to the total height returned
        if self.forks is not None:
            height += self.forks.get_tree_height()

        return height
    
    def get_established_height(self) -> int:
        '''
        Get the height of blocks that are not in forks

        Returns:
            int: The count of the stored and soft stored blocks
        '''

        return self.block_store.height + len(self.blocks)

    def get_top_blockreward(self) -> float:
        '''
        Return the current top block reward
        TODO: Also based on the fork data
        '''

        return self.blockreward
    
    def get_chunk_difficulty(self, chunk_id: int, fork: ForkBlock | None = None) -> int:
        '''
        Depending on the chunk (n blocks where n = settings.difficulty_adjustment)
        Get the corresponding difficulty, based on the previous chunk
        
        Returns:
            int: Difficulty bits
        '''

        if chunk_id == 0: return self.settings.initial_difficulty

        prev_chunk_height = (chunk_id - 1) * self.settings.difficulty_adjustment + 1
        curr_chunk_height = chunk_id * self.settings.difficulty_adjustment

        start: Block | None = self.get_block_by_height(prev_chunk_height, fork)
        end:   Block | None = self.get_block_by_height(curr_chunk_height, fork)

        if (start is None) or (end is None):
            logger.critical(f'Error calculating difficulty of chunk #{chunk_id}')
            return -1

        delta: int = end.timestamp - start.timestamp
        seconds_per_block: float = delta / self.settings.difficulty_adjustment

        # Make sure the spb is never 0
        seconds_per_block = max(seconds_per_block, 0.01)

        deviation: float = self.settings.target_blocktime / seconds_per_block

        # Now we need the previous chunk's difficulty
        prev_chunk_difficulty: int = end.difficulty_bits


        return adjustDifficulty(prev_chunk_difficulty, deviation)

    def get_difficulty(self, forkblock: ForkBlock | None) -> int:
        '''
        Get the difficulty depending on the fork.
        This most often returns just the chain diffulty parameter, but if the 
        difficulty is adjusted within a fork, this is necessary

        Args:
            top_hash (bytes): Hash of which the following difficulty will be returned
            forkblock (ForkBlock): Fork for which the difficulty gets retrieved. None for no fork used
        Returns:
            int: Difficulty bits
        '''
        
        if forkblock is None:
            if self.get_established_height() % self.settings.difficulty_adjustment == 0:
                # This happens when loading the pre stored blockchain from the sote file
                # Just needs to adjust the difficulty
                
                logger.info('Adjusting global difficulty after load')
                newDiff = self.get_chunk_difficulty(self.get_established_height() // self.settings.difficulty_adjustment)
                if newDiff < 0:
                    logger.critical('Difficulty calculation error for new chunk after load')
                    return -1

                self.difficulty = newDiff

            return self.difficulty
        

        route: List[Block] = forkblock.get_block_route()
        route_len: int = len(route)
        fork_height: int = self.get_established_height() + route_len

        established_chunk = (self.get_established_height() - 1) // self.settings.difficulty_adjustment

        chunk_id = fork_height // self.settings.difficulty_adjustment
        
        if established_chunk == chunk_id:
            return self.difficulty

        diff = self.get_chunk_difficulty(chunk_id, forkblock)
        
        return diff

        establ_chunk = (self.get_established_height() - 1) // self.settings.difficulty_adjustment
        forked_chunk = (self.get_established_height() + route_len)         // self.settings.difficulty_adjustment
        
        print('Chunk A:', establ_chunk, 'Chunk B:', forked_chunk)

        if establ_chunk < 0: return self.difficulty

        if not establ_chunk < forked_chunk:
            return self.difficulty
        
        #print('!!! Dynamic difficulty adjustment triggered !!!')

        # Here a difficulty needs to be calculated
        chunk_start = (establ_chunk * self.settings.difficulty_adjustment) + 1
        chunk_end   = forked_chunk * self.settings.difficulty_adjustment
        
        print('Chunk A Height:', chunk_start, 'Chunk B Height:', chunk_end)

        # Get the timestamps of the start and end
        start: Block | None = self.get_block_by_height(chunk_start)

        index = ((self.get_established_height() + route_len) - chunk_end - 1)

        end: Block   | None = route[index]

        if (start is None) or (end is None):
            logger.critical(f"Error calculating diffulty of range {chunk_start} and {chunk_end}")
            return -1

        delta: int = end.timestamp - start.timestamp
        
        seconds_per_block = delta / self.settings.difficulty_adjustment
        seconds_per_block = max(seconds_per_block, 0.01)
        
        deviation = self.settings.target_blocktime / seconds_per_block

        return adjustDifficulty(self.difficulty, deviation)

    def get_top_difficulty(self) -> int:
        '''
        Return the current difficulty bits of the chain
        TODO: Also based on the fork data

        Return:
            int: Difficulty bits
        '''
        
        return self.get_difficulty(self.get_longest_fork()[0])
    
    def get_established_difficulty(self):
        return self.difficulty

    def get_longest_fork(self) -> Tuple[ForkBlock | None, List[Block]]:
        '''
        Returns the current longest fork, including the fork's leaf
        and the block route towards it

        Returns:
            Tuple[ForkBlock, List[Block]]: Leaf and the route
        '''

        if self.forks is None:
            return (None, [])

        cur: ForkBlock = self.forks

        while not len(cur.next) == 0:
            cur = cur.get_tallest_subtree()
        
        route: List[Block] = cur.get_block_route()

        return (cur, route)

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

            if len(self.blocks) == 0 and self.block_store.height > 0:
                # Get the previous hash from the block storage
                return self.block_store.get_store_tophash()

            return self.blocks[-1].hash_sha256() if len(self.blocks) > 0 else b'\x00'*32
        
        current: ForkBlock | None = self.forks 

        while not len(current.next) == 0:
            current = current.get_tallest_subtree()

        return current.block.hash_sha256()
    
    @incomplete
    def verify_chain(self) -> bool:
        '''
        Used to verify the validity of the entire chain, including stored UTXOs

        Returns:
            bool: Whether it's valid or not
        '''
        
        return False

    def save(self) -> None:
        '''
        To be executed before exiting. This stores all established blocks in the storage
        Also saves the UTXO set and (in the future TODO) MemPool
        '''

        logger.debug('Saving data.')
        self.block_store.store_blocks(self.blocks)
        self.blocks.clear()
        
        logger.debug(f'Saved {len(self.blocks)} to block store')

        self.utxo_set.save_utxos()
        self.memory_pool.save_mempool()
