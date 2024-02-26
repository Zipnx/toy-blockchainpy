
from typing import List, Mapping, Type

from coretc.blocks import Block
from coretc.status import BlockStatus
from coretc.utils.list_utils import CombinedList

from binascii import hexlify

class Chain:
    '''
    Chain Core Class 
    Handles the addding of new blocks & verification
    '''

    def __init__(self, initDifficulty: int = 0x200000FF) -> None:
        '''
        Initialize a new chain
        '''
        
        self.initDifficulty = initDifficulty
        self.difficulty = initDifficulty
        self.blocks: List[Block] = [] 

        self.forks: ForkBlock | None = None
    
    def is_block_valid(self, block: Block, additional_chain: List[Block] = []) -> BlockStatus:
        '''
        Given a block, check if it's valid. Also verifies in a side chain

        Return:
            bool: Block validity
        '''
        
        # TODO: Check TXs, for now let's just get this working
        # TODO: Difficulty changes depending on the additional chain, also the UTXO set (to be implemented)
        
        print(len(additional_chain))
        print(additional_chain)

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
        
        if self.forks is not None:
            forkblock: ForkBlock | None = self.forks.get_block_by_hash(newBlock.previous_hash)
        else:
            forkblock = None

        temp_chain_route: List[Block] = []

        if forkblock is not None:
            
            temp_chain_route = forkblock.get_block_route()
        
        validity = self.is_block_valid(newBlock, additional_chain = temp_chain_route)

        if validity == BlockStatus.VALID:
            if newBlock.previous_hash == b'\x00' * 32 and forkblock is None:
                self.forks = ForkBlock(None, newBlock)
                self.forks.hash_cache[newBlock.hash_sha256()] = self.forks

            else:
                if forkblock is None:
                    print('wtf?')
                    return BlockStatus.INVALID_ERROR 

                fb_instance = forkblock.append_block(newBlock)
                self.forks.hash_cache[newBlock.hash_sha256()] = fb_instance

        return validity
        
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
        
        # This is only changed for the root node
        self.hash_cache: Mapping[bytes, ForkBlock] = {}
    
    def append_block(self, new_block: Block):
        '''
        Create a new ForkBlock and add it to the next List
        ! DOES NO VALIDATION, BLOCK MUST BE VALIDATED INDIVIDUALLY
        '''

        new_fb: ForkBlock = ForkBlock(self, new_block)
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

        return max( [ blk.get_tree_height() for blk in self.next ] ) + 1
    
    def is_node_balanced(self) -> bool:
        '''
        Returns true if all child nodes have the same height
        (will return true is there are no child nodes)

        Return:
            bool: Whether the node is balanced
        '''

        if len(self.next) == 0: return True

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

    def _display(self, level: int = 0, prefix: str = 'Root->'):

        print( ('\t'*level) + prefix, f'0x{hexlify(self.block.hash_sha256()).decode()}')

        for i, blk in enumerate(self.next):

            blk._display(level = level + 1, prefix = f'|___{i}->')
