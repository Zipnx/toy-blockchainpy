#!/usr/bin/python3

# Add the proj dir to the PATH to be able to include from coretc
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests import run

if __name__ == '__main__': run()
