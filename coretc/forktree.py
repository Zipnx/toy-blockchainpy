
from typing import List, Tuple
from binascii import hexlify
from copy import deepcopy

from rich.text import Text
from rich.tree import Tree
from rich.panel import Panel
from rich.console import Console

from coretc.blocks import Block
from coretc.transaction import TX
from coretc.utxo import UTXO

import logging

logger = logging.getLogger('tc-core')

class ForkBlock:
    def __init__(self, parent, blk: Block) -> None:
        self.parent: ForkBlock | None = parent
        self.block:  Block = blk
        self.next:   List[ForkBlock] = []
        
        self.utxos_added: List[UTXO] = []
        self.utxos_used:  List[UTXO] = []

        # Note: need to do height recalculation as well as hash cache recalculation 
        self.height: int = 0 # The height of the subtree with this ForkBlock as it's root

        # This is only changed for the root node
        self.hash_cache: dict[bytes, ForkBlock] = {}
        
        # Store used and new utxos from the block
        for transaction in self.block.transactions:
            self.utxos_used.extend(deepcopy(transaction.inputs))
            
            tx_outputs_initial = deepcopy(transaction.outputs)

            for output in tx_outputs_initial:
                output.txid = transaction.get_txid()

            self.utxos_added.extend(tx_outputs_initial)

    
    def append_block(self, new_block: Block):
        '''
        Create a new ForkBlock and add it to the next List, returns a reference to the new object
        ! DOES NO VALIDATION, BLOCK MUST BE VALIDATED INDIVIDUALLY
        
        Updates the heights

        Return:
            ForkBlock: Reference to the new object
        '''
        
        # Create the new forkblock object to use
        new_fb: ForkBlock = ForkBlock(self, new_block)
        
        # Increment the height of all parent nodes if this is now the heighest leaf node of the subtree
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
        current: ForkBlock | None = self
        
        while current is not None:
            blocks.append(current.block)
            
            current = current.parent
        
        blocks.reverse()

        return blocks

    def get_block_route_len(self) -> int:
        '''
        Return the number of total blocks reaching this fork node

        Return:
            int: Length of this fork
        '''

        length: int = 0

        current: ForkBlock | None = self

        while current is not None:
            length += 1
            current = current.parent

        return length

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

    def get_tree_height(self, useCachedHeight: bool = True) -> int:
        '''
        Returns the height of the subtree

        Args:
            useCachedHeight (bool=True): Whether it will use the set height cache or regenerate it
        Return:
            int: Tree height
        '''

        if not useCachedHeight:
            self.regenerate_heights()

        if len(self.next) == 0: return 1

        return self.height + 1

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

        for blk in self.next[1:]:
            
            if not blk.get_tree_height() == cmp_height:
                return False

        return True 
    
    def get_tallest_subtree(self):
        '''
        Return the tallest subtree

        Return:
            ForkBlock: Subtree root node
        '''
        
        # Not actually as inefficient since i changed the height to be stored on the forkblocks
        cur = None
        cur_size: int  = -1

        for blk in self.next:
            
            size = blk.get_tree_height()

            if size >= cur_size:

                cur = blk
                cur_size = size

        return cur
    
    def get_tallest_leaf(self):
        '''
        Return the tallest leaf in this subtree
        Why tf had i not made this earlier
        '''

        current: ForkBlock = self

        while len(current.next) > 0:

            current = max(current.next, key = lambda k: k.height)

        return current
    
    def get_fork_utxoset(self) -> Tuple[List[UTXO], List[UTXO]]:
        '''
        Iterates to it's parent until None and returns a final list of 
        UTXOs in the current fork that have been used and created in the form of a Tuple
        (Note: This is a bit dirty but it should work)

        Return:
            Tuple[List[UTXO], List[UTXO]]: 2 Lists one of the UTXOs used and one with the ones added
        '''
        
        # TODO: High possibility of a bug being here, do unit tests

        result_used:  List[UTXO] = list()
        result_added: List[UTXO] = list()

        cur: ForkBlock = self
        
        #route: List[UTXO] = self.get_block_route()

        while cur is not None:
            
            for used in cur.utxos_used:
                result_used.append(used)

            for added in cur.utxos_added:

                # In case where a UTXO is created inside the fork and used
                if added in result_used:
                    result_used.remove(added)
                    continue

                result_added.append(added)
            
            #print(len(result_used), len(result_added))
            cur = cur.parent
        
        return (result_used, result_added)

    def regenerate_cache(self, start: bool = True) -> dict:
        '''
        Create the hash_cache dict 
        Will improve in the future
        '''
        
        if start:
            logger.info('Regenerating hash cache of fork tree')

        cache = {
            self.block.hash_sha256(): self
        }

        for blk in self.next:
            cache.update(blk.regenerate_cache(start = False))

        if start:
            del self.hash_cache
            self.hash_cache = cache

        return cache
    
    def regenerate_heights(self, start: bool = True) -> int:
        '''
        Recursive function that set's every forkblock's height

        Return:
            int: The whole subtree's height
        '''

        if start:
            logger.info('Recalculating heights in fork tree')

        if len(self.next) == 0:
            self.height = 0
            return 0

        self.height = max( [blk.regenerate_heights(start = False) for blk in self.next] ) + 1
        return self.height

    def _rich_get_tree(self, tree: Tree | None = None) -> Tree:
        
        if tree is None:
            tree = Tree('Fork tree.')
        
        data  = f'Hash: 0x{hexlify(self.block.hash_sha256()).decode()}\n'
        data += f'Prev: 0x{hexlify(self.block.previous_hash).decode()}\n'
        data += f'Fork Height: {self.height}\n'
        data += f'TXs:  {len(self.block.transactions)} | USED UTXOS: {len(self.utxos_used)} | NEW UTXOS: {len(self.utxos_added)}'

        panel = Panel.fit(data)
        
        node = tree.add(panel)
        
        for blk in self.next:
            blk._rich_get_tree(tree = node)

        return node
        

    def _display(self):

        console = Console()
        console.print(self._rich_get_tree())

