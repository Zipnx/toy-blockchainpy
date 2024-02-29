#!/usr/bin/python3

# Add the proj dir to the PATH to be able to include from coretc
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests import run

import logging

logging.getLogger('tc-core').setLevel(logging.ERROR)

if __name__ == '__main__': run()
