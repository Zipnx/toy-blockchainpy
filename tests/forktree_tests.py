
import unittest

from coretc import ForkBlock, Block, mine_block
from coretc import Chain, ChainSettings

from tests.helpers import create_example_block, forktree_from_json

class TestForkTree(unittest.TestCase):

    def test_forktree_getheight(self):

        root = ForkBlock(None, create_example_block())

        self.assertEqual(root.get_tree_height(), 1,
                         "The height at the root of the empty tree should be 1")

        root.append_block(create_example_block(prev = root.block.hash_sha256()))

        root.append_block(create_example_block(prev = root.block.hash_sha256()))

        self.assertEqual(root.get_tree_height(), 2,
                         "Root with 2 children should have height 2")

        self.assertEqual(root.get_children_count(), 2,
                         "Root with 2 children, has, well, 2 children")

        side_a = root.next[0]

        side_a.append_block(create_example_block(prev = side_a.block.hash_sha256()))

        self.assertEqual(root.get_tree_height(), 3,
                         "Expected height 3")

    def test_forktree_structure(self):

        root: ForkBlock = forktree_from_json([[],[[]]])
        #print()
        #root._display()

        self.assertEqual(root.get_tree_height(), 3, 'Height should be 3')
        self.assertEqual(root.get_children_count(), 3, 'Should have 3 children')

        root.next[1].next.clear()
        root.regenerate_heights()
        root.regenerate_cache()

        self.assertEqual(root.get_tree_height(), 2, 'Height should have been lowered to 2')
        self.assertEqual(root.get_tree_height(), 2, 'Child count should be 2')

    def test_forktree_balanced(self):

        root: ForkBlock = forktree_from_json([])
        
        self.assertTrue(root.is_node_balanced(), 'Node with 2 children is inherently balanced')

        root.append_block( create_example_block(prev = root.block.hash_sha256()) )

        self.assertFalse(root.is_node_balanced(), 'Node with 1 child cannot be balanced')

        root.append_block( create_example_block(prev = root.block.hash_sha256()) )

        self.assertTrue(root.is_node_balanced(), 'Node with 2 leaf children must be balanced')

        root = forktree_from_json([[[]],[[]]])

        self.assertTrue(root.is_node_balanced(), 'Should be balanced')

        root = forktree_from_json([[],[[], []]])

        self.assertFalse(root.is_node_balanced(), 'Should not be balanced')

    def test_forktree_linearity(self):

        root: ForkBlock = forktree_from_json([[[[[],[]]]]])

        self.assertEqual(root.get_linear_count(), 3,
                         'The structure has 3 linear forkblocks')

        root: ForkBlock = forktree_from_json([[],[[[[]]]]])

        self.assertEqual(root.get_linear_count(), 0,
                         'Root node is not linear')

        # TODO: This also needs tests
        child = root.get_tallest_subtree()

        self.assertEqual(child.get_linear_count(), 3,
                         'Child node exhibits 3 fold linearity')
