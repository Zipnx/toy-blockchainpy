#!/usr/bin/python3

# Add the proj dir to the PATH to be able to include from coretc
import os, sys
from os.path import exists as fileExists
from os.path import isdir as isDirectory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests import run

import logging

logging.getLogger('tc-core').setLevel(logging.ERROR + 1)

if __name__ == '__main__': 
    store_dir = 'pytests-chain-tmp'

    if not fileExists(store_dir) or not isDirectory(store_dir):
        os.mkdir(store_dir)

    run()

    os.system('rm -r ./pytests-chain-tmp/')
