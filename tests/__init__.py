
import unittest
from tests.chain_tests import TestChain
from tests.json_tests import TestJsonConversion
from tests.mining_tests import TestBlockMining
from tests.misc_tests import TestMisc
from tests.forktree_tests import TestForkTree
from tests.txvalidation_tests import TestTXValidation

def init_test_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestJsonConversion))
    suite.addTest(unittest.makeSuite(TestBlockMining))
    suite.addTest(unittest.makeSuite(TestChain))
    suite.addTest(unittest.makeSuite(TestTXValidation))

    suite.addTest(unittest.makeSuite(TestForkTree))

    suite.addTest(unittest.makeSuite(TestMisc))

    return suite


def run() -> None:
    runner = unittest.TextTestRunner(verbosity = 2)
    suite = init_test_suite()

    runner.run(suite)
