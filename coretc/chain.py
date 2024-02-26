
from typing import List, Mapping, Type

from coretc.blocks import Block
from coretc.status import BlockStatus

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

        self.difficulty = initDifficulty
        self.blocks: List[Block] = [] 

    def add_block(self, newBlock: Block) -> BlockStatus:
        '''
        Try to add a new block in the current chain

        Args:
            newBlock (Block): New block to add

        Return:
            BlockStatus: Status enum, indicates possible errors

        '''

        prevhash = self.get_tophash()

        if not newBlock.previous_hash == prevhash:
            return BlockStatus.INVALID_PREVHASH
        
        if not newBlock.difficulty_bits == self.difficulty:
            return BlockStatus.INVALID_DIFFICULTY

        if not newBlock.is_hash_valid():
            return BlockStatus.INVALID_POW

        self.blocks.append(newBlock)

        return BlockStatus.VALID
        
    def get_current_difficulty(self) -> int:
        '''
        Return the current difficulty bits of the chain

        Return:
            int: Difficulty bits
        '''
        
        return self.difficulty

    def get_tophash(self) -> bytes:
        '''
        Return the current top hash or zero-hash if the chain is empty

        Return:
            bytes: 32 byte hash digest

        '''

        return self.blocks[-1].hash_sha256() if len(self.blocks) > 0 else b'\x00'*32

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
    
    def append_block(self, new_block: Block) -> None:
        '''
        Create a new ForkBlock and add it to the next List
        ! DOES NO VALIDATION, BLOCK MUST BE VALIDATED INDIVIDUALLY
        '''

        new_fb: ForkBlock = ForkBlock(self, new_block)
        self.next.append(new_fb)

    def get_block_by_hash(self, block_hash: bytes):
        '''
        Return the block (if it exists) by it's hash
        ONLY USED BY THE ROOT NODE

        Return:
            ForkBlock: Corresponding fork block
        '''

        if block_hash not in self.hash_cache:
            return None

        return self.hash_cache[block_hash]

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

    def _display(self, level: int = 0, prefix: str = 'Root-> '):

        print( ('\t'*level) + prefix, f'0x{hexlify(self.block.hash_sha256()).decode()}')

        for i, blk in enumerate(self.next):

            blk._display(level = level + 1, prefix = f'|___{i}-> ')

