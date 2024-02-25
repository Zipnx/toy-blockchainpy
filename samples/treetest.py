#!/usr/bin/python3

# Add the ../ directory to PATH to be able to use coretc
import os,sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc import ForkBlock, Block, mine_block

def sample_block(prev) -> Block:

    blk: Block = Block(prev, int(time.time()), 0x200FFFFF, b'', [])
    
    if blk is None:
        exit()

    mine_block(blk)
    
    return blk

def add_to_fork(node: ForkBlock):

    node.next.append(ForkBlock(node, sample_block(node.block.hash_sha256())))

def main():

    root = ForkBlock(None, sample_block(b'\x00'*32))
    
    add_to_fork(root)
    add_to_fork(root)

    side_a = root.next[0]
    side_b = root.next[1]
    
    add_to_fork(side_a)
    add_to_fork(side_b)
    add_to_fork(side_a.next[-1])
    add_to_fork(side_a.next[-1])

    
    print(root.get_children_count())
    print(root.get_tree_height())
    
    root._display()

    print()

    x: ForkBlock = root.get_tallest_subtree()

    x._display()

    print()

    x.get_tallest_subtree()._display()


if __name__ == '__main__':
    main()
