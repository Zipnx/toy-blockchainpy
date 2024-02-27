
from enum import nonmember
from typing import List, Mapping, Type

from coretc.blocks import Block
from coretc.utxo import UTXO
from coretc.status import BlockStatus
from coretc.utils.list_utils import CombinedList
from coretc.settings import ChainSettings
from coretc.utxoset import UTXOSet

from binascii import hexlify
import json, time

class Chain:
    '''
    Chain Core Class 
    Handles the addding of new blocks & verification
    '''

    def __init__(self, settings: ChainSettings) -> None:
        '''
        Initialize a new chain
        '''
        
        self.opts = settings

        self.initDifficulty = settings.initial_difficulty
        self.difficulty = settings.initial_difficulty
        self.blocks: List[Block] = [] 

        self.forks: ForkBlock | None = None

        self.utxo_set: UTXOSet = UTXOSet(self.opts.utxo_set_path)
        
        # TODO: Do checks here
        self.utxo_set.load_utxos()

    
    def is_block_valid(self, block: Block, additional_chain: List[Block] = []) -> BlockStatus:
        '''
        Given a block, check if it's valid. Also verifies in a side chain

        Return:
            bool: Block validity
        '''
        
        # TODO: Check if the block is a duplicate (check the .next of the forkblock)
        # TODO: Check TXs, for now let's just get this working
        # TODO: Difficulty changes depending on the additional chain, also the UTXO set (to be implemented)
        
        reference_chain: CombinedList = CombinedList(self.blocks, additional_chain)

        if len(reference_chain) == 0:

            if not block.previous_hash == b'\x00'*32: 
                return BlockStatus.INVALID_PREVHASH

            if not block.difficulty_bits == self.initDifficulty:
                return BlockStatus.INVALID_DIFFICULTY

            if not block.is_hash_valid():
                return BlockStatus.INVALID_POW

            return BlockStatus.VALID

        if not block.previous_hash == reference_chain[-1].hash_sha256():
            return BlockStatus.INVALID_PREVHASH

        if not block.difficulty_bits == self.difficulty:
            return BlockStatus.INVALID_DIFFICULTY

        if not block.is_hash_valid():
            return BlockStatus.INVALID_POW

        return BlockStatus.VALID

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

        temp_chain_route: List[Block] = []
        
        if forkblock is not None:
            
            temp_chain_route = forkblock.get_block_route()
        
        validity = self.is_block_valid(newBlock, additional_chain = temp_chain_route)
        
        ### If the block is valid it will either be added as the new fork tree root 
        ### (if it's the first block) or it gets added to the tree

        if validity == BlockStatus.VALID:
            if newBlock.previous_hash == b'\x00' * 32 and forkblock is None:
                self.forks = ForkBlock(None, newBlock)

                # i hate myself i hate myself i hate myself
                self.forks.hash_cache[newBlock.hash_sha256()] = self.forks

            else:
                if forkblock is None:
                    print('wtf?')
                    return BlockStatus.INVALID_ERROR 

                fb_instance = forkblock.append_block(newBlock)
                self.forks.hash_cache[newBlock.hash_sha256()] = fb_instance
            
            merged = self.attempt_merge()

            print(f'Merged {merged} blocks.')

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
        
        if linear_height >= 3:
            for _ in range(linear_height - 1):
                self.forks = self.forks.next[0]
            
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
        
        self.forks = current
        self.forks.regenerate_heights()
        self.forks.regenerate_cache() # Performance hit

        return mergers



    def get_top_difficulty(self) -> int:
        '''
        Return the current difficulty bits of the chain

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
            return self.blocks[-1].hash_sha256() if len(self.blocks) > 0 else b'\x00'*32
        
        current: ForkBlock = self.forks 

        while not len(current.next) == 0:
            current = current.get_tallest_subtree()

        return current.block.hash_sha256()

class ForkBlock:
    '''
    ForkBlock class, used to represent blocks not yet permanently added to the blockchain
    Forms a tree structure

    After the tree has reached a certain height (merge len), 
    a number of blocks (merged block count) get added to the blockchain permanently, 
    and the tree gets restructured to a subtree of height merge_len - merged block count
    '''

    def __init__(self, parent, blk: Block):
        '''
        Initialize a new fork block object using a block and it's predecessor in the chain
        
        TODO: Alot can be done to make this more speed efficient
        '''
        
        self.parent: ForkBlock = parent
        self.block:  Block = blk
        self.next:   List[ForkBlock] = []
        
        self.utxos_added: List[UTXO] = []
        self.utxos_used:  List[UTXO] = []

        # Note: need to do height recalculation as well as hash cache recalculation 
        self.height: int = 0 # The height of the subtree with this ForkBlock as it's root

        # This is only changed for the root node
        self.hash_cache: Mapping[bytes, ForkBlock] = {}
    
    def append_block(self, new_block: Block):
        '''
        Create a new ForkBlock and add it to the next List, returns a reference to the new object
        ! DOES NO VALIDATION, BLOCK MUST BE VALIDATED INDIVIDUALLY
        
        Return:
            ForkBlock: Reference to the new object
        '''

        new_fb: ForkBlock = ForkBlock(self, new_block)

        if len(self.next) == 0:
            
            cur: ForkBlock = self
            
            while cur is not None:
                cur.height += 1
                cur = cur.parent
    

        self.next.append(new_fb)

        return new_fb
    
    def block_hash_exists(self, block_hash: bytes) -> bool:
        '''
        Given a Block's hash, check if it exists in the hash cache of the fork tree

        Return:
            bool: Existance of the block
        '''

        return block_hash in self.hash_cache

    def get_block_by_hash(self, block_hash: bytes):
        '''
        Return the block (if it exists) by it's hash
        ONLY USED BY THE ROOT NODE

        Return:
            ForkBlock: Corresponding fork block
        '''
        
        #print(self.hash_cache)
        #print(block_hash)

        if block_hash not in self.hash_cache:
            return None

        return self.hash_cache[block_hash]
    
    def get_linear_count(self) -> int:
        '''
        Get a count for tree levels that are "linear", ie only have one element in the .next list

        Return:
            int: Count of linear levels
        '''

        current: ForkBlock = self
        linear_count: int = 0

        while (len(current.next) == 1):
            linear_count += 1
            current = current.next[0]

        return linear_count

    def get_block_route(self) -> List[Block]:
        '''
        Return the list of Blocks forming a path to this node in the fork tree

        Return:
            List[Block]: List of blocks in the path
        '''

        blocks: List[Block] = []
        current: ForkBlock = self
        
        while current is not None:
            blocks.append(current.block)
            
            current = current.parent
        
        blocks.reverse()

        return blocks

        

    def get_children_count(self) -> int:
        '''
        Return the number of chidren ForkBlock nodes
        
        Return:
            int: Count of total children in sub tree
        '''
        
        count = len(self.next)

        for blk in self.next:
            count += blk.get_children_count()

        return count

    def get_tree_height(self) -> int:
        '''
        Return the height of the subtree

        Return:
            int: Tree height
        '''
        
        if len(self.next) == 0: return 1
        
        return self.height
        #return max( [ blk.get_tree_height() for blk in self.next ] ) + 1
    
    def is_node_balanced(self) -> bool:
        '''
        Returns true if all child nodes have the same height
        (will return true is there are no child nodes)

        Return:
            bool: Whether the node is balanced
        '''

        if len(self.next) == 0: return True
        if len(self.next) == 1: return False

        cmp_height = self.next[0].get_tree_height()

        for blk in self.next: # yes, the start node doesnt need to be checked, will fix sometime
            
            if not blk.get_tree_height() == cmp_height:
                return False

        return True


    def get_tallest_subtree(self):
        '''
        Return the tallest subtree

        Return:
            ForkBlock: Subtree root node
        '''
        
        cur = None
        cur_size: int  = -1

        for blk in self.next:
            
            size = blk.get_tree_height()

            if size >= cur_size:

                cur = blk
                cur_size = size

        return cur
    
    def regenerate_cache(self, start: bool = True) -> dict:
        '''
        Create the hash_cache dict 
        Will improve in the future
        '''

        cache = {
            self.block.hash_sha256(): self
        }

        for blk in self.next:
            cache.update(blk.regenerate_cache(start = False))

        if start:
            del self.hash_cache
            self.hash_cache = cache

        return cache
        
    def regenerate_heights(self) -> int:
        '''
        Recursive function that set's every forkblock's height

        Return:
            int: The whole subtree's height
        '''

        if len(self.next) == 0:
            self.height = 1
            return 1

        self.height = max( [blk.regenerate_heights() for blk in self.next] )
        return self.height


    def _display(self, level: int = 0, prefix: str = 'Root->'):

        print( ('\t'*level) + prefix, f'0x{hexlify(self.block.hash_sha256()).decode()}')

        for i, blk in enumerate(self.next):

            blk._display(level = level + 1, prefix = f'|___{i}->')

