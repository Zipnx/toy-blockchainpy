
import unittest
from tests.json_tests import TestJsonConversion
from tests.mining_tests import TestBlockMining
from tests.misc_tests import TestMisc

def init_test_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestJsonConversion))
    suite.addTest(unittest.makeSuite(TestBlockMining))
    suite.addTest(unittest.makeSuite(TestMisc))

    return suite


def run():
    runner = unittest.TextTestRunner(verbosity = 2)
    suite = init_test_suite()

    runner.run(suite)
